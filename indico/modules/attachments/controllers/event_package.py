# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os
from collections import OrderedDict

from celery.exceptions import TimeoutError
from flask import flash, jsonify, request, session
from markupsafe import escape
from sqlalchemy import Date, cast

from indico.core.celery import AsyncResult
from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.errors import IndicoError
from indico.modules.attachments.forms import AttachmentPackageForm
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.tasks import generate_materials_package
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.util import ZipGeneratorMixin
from indico.util.date_time import format_date, format_time
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.string import natural_sort_key, to_unicode
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data


def _get_start_dt(obj):
    # TODO: adapt to new models (needs extra properties to use event TZ)
    if isinstance(obj, Contribution):
        return obj.timetable_entry.start_dt if obj.timetable_entry else None
    elif isinstance(obj, SubContribution):
        return obj.timetable_entry.start_dt if obj.timetable_entry else None
    elif isinstance(obj, Session):
        return None
    return obj.start_dt


def _get_obj_parent(obj):
    if isinstance(obj, SubContribution):
        return obj.contribution
    elif isinstance(obj, Contribution):
        return obj.session or obj.event
    return obj.event


class AttachmentPackageGeneratorMixin(ZipGeneratorMixin):

    #: Whether unscheduled contributions should be included
    ALLOW_UNSCHEDULED = False

    def _filter_attachments(self, filter_data):
        added_since = filter_data.get('added_since', None)
        filter_type = filter_data['filter_type']
        attachments = []

        if filter_type == 'all':
            attachments = self._get_all_attachments(added_since)
        elif filter_type == 'sessions':
            attachments = self._filter_by_sessions(filter_data.get('sessions', []), added_since)
        elif filter_type == 'contributions':
            attachments = self._filter_by_contributions(filter_data.get('contributions', []), added_since)
        elif filter_type == 'dates':
            attachments = self._filter_by_dates(filter_data.get('dates', []))

        return self._filter_protected(attachments)

    def _filter_protected(self, attachments):
        return [attachment for attachment in attachments if attachment.can_access(session.user)]

    def _get_all_attachments(self, added_since):
        query = self._build_base_query(added_since)
        return [attachment for attachment in query if _get_start_dt(attachment.folder.object) is not None]

    def _build_base_query(self, added_since=None):
        query = Attachment.find(Attachment.type == AttachmentType.file, ~AttachmentFolder.is_deleted,
                                ~Attachment.is_deleted, AttachmentFolder.event == self.event,
                                _join=AttachmentFolder)
        if added_since is not None:
            query = query.join(Attachment.file).filter(cast(AttachmentFile.created_dt, Date) >= added_since)
        return query

    def _filter_by_sessions(self, session_ids, added_since):
        sid_query = Contribution.session_id.in_(set(session_ids))
        session_query = db.and_(AttachmentFolder.link_type == LinkType.session,
                                AttachmentFolder.session.has(Session.id.in_(session_ids) & ~Session.is_deleted))
        contrib_query = db.and_(AttachmentFolder.link_type == LinkType.contribution,
                                AttachmentFolder.contribution.has(sid_query & ~Contribution.is_deleted))
        subcontrib_query = db.and_(AttachmentFolder.link_type == LinkType.subcontribution,
                                   AttachmentFolder.subcontribution.has(
                                       sid_query & ~SubContribution.is_deleted & ~Contribution.is_deleted))

        return self._build_base_query(added_since).filter(db.or_(session_query, contrib_query, subcontrib_query)).all()

    def _filter_by_contributions(self, contribution_ids, added_since):
        query = self._build_base_query(added_since).filter(AttachmentFolder.link_type.in_([LinkType.contribution,
                                                                                           LinkType.subcontribution]))
        objs = []
        for attachment in query:
            linked_obj = attachment.folder.object
            if linked_obj.is_deleted:
                continue
            if (isinstance(linked_obj, SubContribution) and not linked_obj.contribution.is_deleted and
                    linked_obj.contribution_id in contribution_ids):
                objs.append(attachment)
            elif isinstance(linked_obj, Contribution) and linked_obj.id in contribution_ids:
                objs.append(attachment)

        return [attachment for attachment in objs
                if self.ALLOW_UNSCHEDULED or _get_start_dt(attachment.folder.object) is not None]

    def _filter_by_dates(self, dates):
        dates = set(dates)

        def _check_date(attachment):
            start_dt = _get_start_dt(attachment.folder.object)
            if start_dt is None:
                return None
            return unicode(start_dt.date()) in dates

        return filter(_check_date, self._build_base_query())

    def _iter_items(self, attachments):
        for attachment in attachments:
            yield attachment.file

    def _prepare_folder_structure(self, item):
        attachment = item.attachment
        event_dir = secure_filename(self.event.title, None)
        segments = [event_dir] if event_dir else []
        if _get_start_dt(attachment.folder.object) is None:
            segments.append('Unscheduled')
        segments.extend(self._get_base_path(attachment))
        if not attachment.folder.is_default:
            segments.append(secure_filename(attachment.folder.title, unicode(attachment.folder.id)))
        segments.append(attachment.file.filename)
        path = os.path.join(*self._adjust_path_length(filter(None, segments)))
        while path in self.used_filenames:
            # prepend the id if there's a path collision
            segments[-1] = '{}-{}'.format(attachment.id, segments[-1])
            path = os.path.join(*self._adjust_path_length(filter(None, segments)))
        return path

    def _get_base_path(self, attachment):
        # TODO: adapt to new models (needs extra properties to use event TZ)
        obj = linked_object = attachment.folder.object
        paths = []
        while obj != self.event:
            start_date = _get_start_dt(obj)
            if start_date is not None:
                if isinstance(obj, SubContribution):
                    paths.append(secure_filename('{}_{}'.format(obj.position, obj.title), ''))
                else:
                    time = format_time(start_date, format='HHmm', timezone=self.event.timezone)
                    paths.append(secure_filename('{}_{}'.format(to_unicode(time), obj.title), ''))
            else:
                if isinstance(obj, SubContribution):
                    paths.append(secure_filename('{}_{}'.format(obj.position, obj.title), unicode(obj.id)))
                else:
                    paths.append(secure_filename(obj.title, unicode(obj.id)))
            obj = _get_obj_parent(obj)

        linked_obj_start_date = _get_start_dt(linked_object)
        if attachment.folder.object != self.event and linked_obj_start_date is not None:
            paths.append(secure_filename(linked_obj_start_date.strftime('%Y%m%d_%A'), ''))

        return reversed(paths)


class AttachmentPackageMixin(AttachmentPackageGeneratorMixin):
    wp = None
    management = False

    def _process(self):
        form = self._prepare_form()
        if form.validate_on_submit():
            attachments = [attachment.id for attachment in self._filter_attachments(form.data)]
            if attachments:
                task = generate_materials_package.delay(attachments, self.event)
                return jsonify(task_id=task.id, success=True)
            else:
                flash(_('There are no materials matching your criteria.'), 'warning')
                return jsonify_data(success=False)
        elif form.is_submitted():
            flash('; '.join(form.error_list), 'warning')
            return jsonify_data(success=False)

        return self.wp.render_template('generate_package.html', self.event, form=form, management=self.management)

    def _prepare_form(self):
        form = AttachmentPackageForm(obj=FormDefaults(filter_type='all'))
        form.dates.choices = list(self._iter_event_days())
        filter_types = OrderedDict()
        filter_types['all'] = _('Everything')
        filter_types['sessions'] = _('Specific sessions')
        filter_types['contributions'] = _('Specific contributions')
        filter_types['dates'] = _('Specific days')

        form.sessions.choices = self._load_session_data()
        if not form.sessions.choices:
            del filter_types['sessions']
            del form.sessions

        form.contributions.choices = self._load_contribution_data()
        if not form.contributions.choices:
            del filter_types['contributions']
            del form.contributions

        form.filter_type.choices = filter_types.items()
        return form

    def _load_session_data(self):
        return [(sess.id, escape(sess.title)) for sess in self.event.sessions]

    def _load_contribution_data(self):
        def _format_contrib(contrib):
            if contrib.session is None:
                return contrib.title
            else:
                return _('{contrib} (in session "{session}")').format(
                    session=contrib.session.title,
                    contrib=contrib.title
                )

        contribs = sorted([contrib for contrib in self.event.contributions if contrib.timetable_entry],
                          key=lambda c: natural_sort_key(c.title))
        return [(contrib.id, escape(_format_contrib(contrib))) for contrib in contribs]

    def _iter_event_days(self):
        for day in self.event.iter_days():
            yield day.isoformat(), format_date(day, 'short').decode('utf-8')


class RHPackageEventAttachmentsStatus(RHDisplayEventBase):
    def _process(self):
        res = AsyncResult(request.view_args['task_id'])
        try:
            download_url = res.get(5, propagate=False)
        except TimeoutError:
            return jsonify(download_url=None)
        try:
            if res.successful():
                return jsonify(download_url=download_url)
            else:
                raise IndicoError(_('Material package generation failed'))
        finally:
            res.forget()
