# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import os
from collections import OrderedDict
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from flask import session, flash
from sqlalchemy import cast, Date

from indico.core.config import Config
from indico.core.db.sqlalchemy.links import LinkType
from indico.util.date_time import format_date
from indico.util.i18n import _
from indico.util.fs import secure_filename
from indico.util.string import to_unicode
from indico.util.tasks import delete_file
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.modules.attachments.forms import AttachmentPackageForm
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from MaKaC.conference import SubContribution


def _get_start_date(obj):
    if isinstance(obj, SubContribution):
        return obj.getContribution().getAdjustedStartDate()
    else:
        return obj.getAdjustedStartDate()


class AttachmentPackageGeneratorMixin:

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
            attachments = self._filter_by_dates(filter_data.get('dates'))

        return self._filter_protected(attachments)

    def _filter_protected(self, attachments):
        return [attachment for attachment in attachments if attachment.can_access(session.user)]

    def _get_all_attachments(self, added_since):
        query = self._build_base_query()

        if added_since:
            query = self._filter_by_date(query, added_since)

        return [att for att in query if att.folder.linked_object and _get_start_date(att.folder.linked_object)]

    def _build_base_query(self):
        return Attachment.find(Attachment.type == AttachmentType.file, ~AttachmentFolder.is_deleted,
                               ~Attachment.is_deleted, AttachmentFolder.event_id == int(self._conf.getId()),
                               _join=AttachmentFolder)

    def _filter_by_sessions(self, session_ids, added_since):
        query = self._build_base_query().filter(AttachmentFolder.link_type.in_([LinkType.session, LinkType.contribution,
                                                                                LinkType.subcontribution]))

        if added_since:
            query = self._filter_by_date(query, added_since)

        return [att for att in query if att.folder.linked_object.getSession()
                and att.folder.linked_object.getSession().getId() in session_ids]

    def _filter_by_contributions(self, contribution_ids, added_since):
        query = self._build_base_query().filter(AttachmentFolder.contribution_id.in_(contribution_ids),
                                                AttachmentFolder.link_type.in_([LinkType.contribution,
                                                                                LinkType.subcontribution]))

        if added_since:
            query = self._filter_by_date(query, added_since)

        return [att for att in query if att.folder.linked_object and _get_start_date(att.folder.linked_object)]

    def _filter_by_dates(self, dates):
        return [att for att in self._build_base_query() if att.folder.linked_object and
                unicode(_get_start_date(att.folder.linked_object)) in dates]

    def _filter_by_date(self, query, added_since):
        return query.join(Attachment.file).filter(cast(AttachmentFile.created_dt, Date) >= added_since)

    def _generate_zip_file(self, attachments):
        temp_file = NamedTemporaryFile(suffix='indico.tmp', dir=Config.getInstance().getTempDir())
        with ZipFile(temp_file.name, 'w', allowZip64=True) as zip_handler:
            self.used = set()
            for attachment in attachments:
                name = self._prepare_folder_structure(attachment)
                self.used.add(name)
                with attachment.file.storage.get_local_path(attachment.file.storage_file_id) as filepath:
                    zip_handler.write(filepath, name)

        # Delete the temporary file after some time.  Even for a large file we don't
        # need a higher delay since the webserver will keep it open anyway until it's
        # done sending it to the client.
        delete_file.apply_async(args=[temp_file.name], countdown=3600)
        temp_file.delete = False
        return send_file('material-{}.zip'.format(self._conf.id), temp_file.name, 'application/zip', inline=False)

    def _prepare_folder_structure(self, attachment):
        event_dir = secure_filename(self._conf.getTitle(), None)
        segments = [event_dir] if event_dir else []
        segments.extend(self._get_base_path(attachment))
        if not attachment.folder.is_default:
            segments.append(secure_filename(attachment.folder.title, unicode(attachment.folder.id)))
        segments.append(attachment.file.filename)
        path = os.path.join(*filter(None, segments))
        while path in self.used:
            # prepend the id if there's a path collision
            segments[-1] = '{}-{}'.format(attachment.id, segments[-1])
            path = os.path.join(*filter(None, segments))
        return path

    def _get_base_path(self, attachment):
        obj = linked_object = attachment.folder.linked_object
        paths = []
        while obj != self._conf:
            owner = obj.getOwner()
            if isinstance(obj, SubContribution):
                start_date = owner.getAdjustedStartDate()
            else:
                start_date = obj.getAdjustedStartDate()

            if start_date is not None:
                paths.append(secure_filename(start_date.strftime('%H%M_{}').format(obj.getTitle()), ''))
            else:
                paths.append(secure_filename(obj.getTitle(), unicode(obj.getId())))
            obj = owner

        if isinstance(linked_object, SubContribution):
            linked_obj_start_date = linked_object.getOwner().getAdjustedStartDate()
        else:
            linked_obj_start_date = linked_object.getAdjustedStartDate()

        if attachment.folder.linked_object != self._conf and linked_obj_start_date is not None:
            paths.append(secure_filename(linked_obj_start_date.strftime('%Y%m%d_%A'), ''))

        return reversed(paths)


class AttachmentPackageMixin(AttachmentPackageGeneratorMixin):
    wp = None

    def _process(self):
        form, skipped_fields = self._prepare_form()
        if form.validate_on_submit():
            attachments = self._filter_attachments(form.data)
            if attachments:
                return self._generate_zip_file(attachments)
            else:
                flash(_('There are no materials matching your criteria.'), 'warning')

        return self.wp.render_template('generate_package.html', self._conf, form=form, skipped_fields=skipped_fields)

    def _prepare_form(self):
        form = AttachmentPackageForm(obj=FormDefaults(filter_type='all'))
        filter_types = OrderedDict(all=_('Everything'))
        sessions = self._load_session_data()
        contributions = self._load_contribution_data()
        dates = self._load_dates()

        if sessions:
            filter_types['sessions'] = _('Specific sessions')
        if contributions:
            filter_types['contributions'] = _('Specific contributions')
        if dates:
            filter_types['dates'] = _('Specific days')

        skipped_fields = {'sessions', 'contributions', 'dates'} - filter_types.viewkeys()
        form.filter_type.choices = filter_types.items()
        form.sessions.choices = sessions
        form.contributions.choices = contributions
        form.dates.choices = dates
        return form, skipped_fields

    def _load_session_data(self):
        return [(session.getId(), to_unicode(session.getTitle())) for session in self._conf.getSessionList()]

    def _load_contribution_data(self):
        return [(contrib.getId(), to_unicode(contrib.getTitle()))
                for contrib in self._conf.getContributionList() if contrib.getOwner() == self._conf
                and contrib.getStartDate()]

    def _load_dates(self):
        offset = self._conf.getAdjustedEndDate() - self._conf.getAdjustedStartDate()
        return [(unicode(self._conf.getAdjustedStartDate() + datetime.timedelta(days=day_number)),
                 format_date(self._conf.getAdjustedStartDate() + datetime.timedelta(days=day_number), 'short'))
                for day_number in xrange(offset.days + 1)]
