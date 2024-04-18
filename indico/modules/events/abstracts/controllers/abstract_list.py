# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict
from operator import attrgetter

from flask import flash, jsonify, request, session
from sqlalchemy.orm import joinedload, subqueryload
from webargs import fields

from indico.core.db import db
from indico.modules.events.abstracts.controllers.base import RHManageAbstractsBase
from indico.modules.events.abstracts.controllers.common import (AbstractsDownloadAttachmentsMixin, AbstractsExportCSV,
                                                                AbstractsExportExcel, AbstractsExportPDFMixin,
                                                                CustomizeAbstractListMixin, DisplayAbstractListMixin)
from indico.modules.events.abstracts.forms import BulkAbstractJudgmentForm
from indico.modules.events.abstracts.lists import AbstractListGeneratorManagement
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.operations import create_abstract, delete_abstract, judge_abstract
from indico.modules.events.abstracts.schemas import abstract_review_questions_schema, abstracts_schema
from indico.modules.events.abstracts.util import can_create_invited_abstracts, make_abstract_form
from indico.modules.events.abstracts.views import WPManageAbstracts
from indico.modules.events.cloning import get_attrs_to_clone
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.management.controllers.emails import (EmailRolesMetadataMixin, EmailRolesPreviewMixin,
                                                                 EmailRolesSendMixin)
from indico.modules.events.persons.util import get_event_person_for_user
from indico.modules.events.registration.util import get_registered_event_persons
from indico.modules.events.util import get_field_values
from indico.modules.users.models.users import User
from indico.util.i18n import _, ngettext
from indico.web.args import use_kwargs
from indico.web.util import jsonify_data, jsonify_form


class RHAbstractListBase(RHManageAbstractsBase):
    """Base class for all RHs using the abstract list generator."""

    def _process_args(self):
        RHManageAbstractsBase._process_args(self)
        self.list_generator = AbstractListGeneratorManagement(event=self.event)


class RHManageAbstractsActionsBase(RHAbstractListBase):
    """Base class for RHs performing actions on selected abstracts."""

    _abstract_query_options = ()
    _allow_get_all = False

    @property
    def _abstract_query(self):
        query = Abstract.query.with_parent(self.event)
        if self._abstract_query_options:
            query = query.options(*self._abstract_query_options)
        return query

    @use_kwargs({
        'abstract_ids': fields.List(fields.Int(), data_key='abstract_id', load_default=lambda: [])
    })
    def _process_args(self, abstract_ids):
        RHAbstractListBase._process_args(self)
        query = self._abstract_query
        if request.method == 'POST' or not self._allow_get_all:
            # if it's POST we filter by abstract ids; otherwise we assume
            # the user wants everything (e.g. API-like usage via personal token)
            query = query.filter(Abstract.id.in_(abstract_ids))
        self.abstracts = query.all()


class RHBulkAbstractJudgment(RHManageAbstractsActionsBase):
    """Perform bulk judgment operations on selected abstracts."""

    def _process(self):
        form = BulkAbstractJudgmentForm(event=self.event, abstract_id=[a.id for a in self.abstracts],
                                        judgment=request.form.get('judgment'))
        if form.validate_on_submit():
            judgment_data, abstract_data = form.split_data
            submitted_abstracts = {abstract for abstract in self.abstracts if abstract.state == AbstractState.submitted}
            num_skipped_abstracts = sum(not judge_abstract(abstract, abstract_data, judge=session.user, **judgment_data)
                                        for abstract in submitted_abstracts)
            num_judged_abstracts = len(submitted_abstracts) - num_skipped_abstracts
            num_prejudged_abstracts = len(self.abstracts) - len(submitted_abstracts)
            if num_judged_abstracts:
                flash(ngettext('{num} abstract has been judged.',
                               '{num} abstracts have been judged.',
                               num_judged_abstracts).format(num=num_judged_abstracts), 'success')
            if num_prejudged_abstracts:
                flash(ngettext('{num} abstract has been skipped since it is already judged.',
                               '{num} abstracts have been skipped since they are already judged.',
                               num_prejudged_abstracts).format(num=num_prejudged_abstracts), 'warning')
            if num_skipped_abstracts:
                flash(ngettext('{num} abstract has been skipped since it was under review for more than one track.',
                               '{num} abstracts have been skipped since they were under review for more than one '
                               'track.',
                               num_skipped_abstracts).format(num=num_skipped_abstracts), 'warning')
            return jsonify_data(**self.list_generator.render_list())
        return jsonify_form(form=form, fields=form._order, submit=_('Judge'), disabled_until_change=False)


class RHAbstractList(DisplayAbstractListMixin, RHAbstractListBase):
    template = 'management/abstract_list.html'
    view_class = WPManageAbstracts

    def _render_template(self, **kwargs):
        kwargs['track_session_map'] = {track.id: track.default_session_id for track in self.event.tracks}
        can_create = can_create_invited_abstracts(self.event)
        return super()._render_template(can_create_invited_abstracts=can_create, **kwargs)


class RHAbstractListCustomize(CustomizeAbstractListMixin, RHAbstractListBase):
    view_class = WPManageAbstracts
    ALLOW_LOCKED = True


class RHAbstractListStaticURL(RHAbstractListBase):
    """Generate a static URL for the configuration of the abstract list."""

    ALLOW_LOCKED = True

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHCreateAbstract(RHAbstractListBase):
    """Create an abstract from scratch or with existing cloned data."""

    def clone_fields(self, abstract):
        field_names = ['title', 'description', 'submission_comment', 'submitted_for_tracks', 'submitted_contrib_type']
        field_data = {f: getattr(abstract, f) for f in field_names}
        person_links = []
        link_attrs = get_attrs_to_clone(AbstractPersonLink)
        for old_link in abstract.person_links:
            link = AbstractPersonLink(person=old_link.person)
            link.populate_from_attrs(old_link, link_attrs)
            person_links.append(link)
        field_data['person_links'] = person_links
        for f in abstract.field_values:
            field_data[f'custom_{f.contribution_field_id}'] = f.data
        return field_data

    @use_kwargs({
        'abstract_id': fields.Int(load_default=None)
    }, location='query')
    def _process_args(self, abstract_id):
        RHAbstractListBase._process_args(self)
        self.abstract = None
        if abstract_id:
            self.abstract = Abstract.query.with_parent(self.event).filter_by(id=abstract_id).first_or_404()

    def _process(self):
        is_invited = request.args.get('invited') == '1'
        abstract_form_class = make_abstract_form(self.event, session.user, notification_option=True,
                                                 management=self.management, invited=is_invited)
        cloned_fields = self.clone_fields(self.abstract) if self.abstract else {}
        form = abstract_form_class(event=self.event, management=self.management, invited=is_invited, **cloned_fields)
        if is_invited:
            del form.submitted_contrib_type
            del form.attachments
            del form.send_notifications
            del form.person_links

        if form.validate_on_submit():
            data = form.data
            submitter = None
            if is_invited:
                if form.users_with_no_account.data == 'existing':
                    submitter = data['submitter']
                else:
                    submitter = User(first_name=data['first_name'], last_name=data['last_name'], email=data['email'],
                                     is_pending=True)
                    db.session.add(submitter)
                    db.session.flush()

                data.pop('first_name')
                data.pop('last_name')
                data.pop('email')
                data.pop('users_with_no_account')
                data.pop('submitter')

            send_notifications = data.pop('send_notifications', is_invited)
            abstract, __ = create_abstract(self.event, *get_field_values(data), send_notifications=send_notifications,
                                           submitter=submitter, is_invited=is_invited)
            flash(_("Abstract '{}' created successfully").format(abstract.title), 'success')
            tpl_components = self.list_generator.render_list(abstract)
            if tpl_components.get('hide_abstract'):
                self.list_generator.flash_info_message(abstract)
            return jsonify_data(**tpl_components)
        return jsonify_form(form, back=_('Cancel'), disabled_until_change=(not self.abstract or is_invited),
                            form_header_kwargs={'action': request.relative_url})


class RHDeleteAbstracts(RHManageAbstractsActionsBase):
    def _process(self):
        delete_contribs = request.values.get('delete_contribs') == '1'
        deleted_contrib_count = 0
        for abstract in self.abstracts:
            if delete_contribs and abstract.contribution:
                deleted_contrib_count += 1
            delete_abstract(abstract, delete_contribs)
        deleted_abstract_count = len(self.abstracts)
        flash(ngettext('The abstract has been deleted.',
                       '{count} abstracts have been deleted.', deleted_abstract_count)
              .format(count=deleted_abstract_count), 'success')
        if deleted_contrib_count:
            flash(ngettext('The linked contribution has been deleted.',
                           '{count} linked contributions have been deleted.', deleted_contrib_count)
                  .format(count=deleted_contrib_count), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHAbstractPersonList(RHManageAbstractsActionsBase):
    """List of persons somehow related to abstracts (co-authors, speakers...)."""

    ALLOW_LOCKED = True

    @property
    def _membership_filter(self):
        abstract_ids = {abstract.id for abstract in self.abstracts}
        return Abstract.id.in_(abstract_ids)

    def _process(self):
        def _get_or_create_person_dict(person):
            person_dict = abstract_persons_dict[person.identifier]
            person_dict['identifier'] = person.identifier
            person_dict['full_name'] = person.display_full_name
            person_dict['email'] = person.email
            person_dict['affiliation'] = person.affiliation
            return person_dict

        submitters = {abstract.submitter for abstract in self.abstracts}
        abstract_persons = (AbstractPersonLink.query
                            .filter(AbstractPersonLink.abstract.has(self._membership_filter))
                            .all())
        registered_persons = get_registered_event_persons(self.event)
        abstract_persons_dict = defaultdict(lambda: {'speaker': False, 'submitter': False, 'primary_author': False,
                                                     'secondary_author': False})
        for abstract_person in abstract_persons:
            user_or_person = abstract_person.person.user or abstract_person.person
            person_dict = _get_or_create_person_dict(user_or_person)
            person_dict['speaker'] |= abstract_person.is_speaker
            person_dict['primary_author'] |= abstract_person.author_type == AuthorType.primary
            person_dict['secondary_author'] |= abstract_person.author_type == AuthorType.secondary
            person_dict['registered'] = abstract_person.person in registered_persons
        for submitter in submitters:
            person_dict = _get_or_create_person_dict(submitter)
            person_dict['submitter'] = True
            person_dict['registered'] = get_event_person_for_user(self.event, submitter) in registered_persons
        return jsonify(event_persons=abstract_persons_dict)


class RHManageAbstractsExportActionsBase(RHManageAbstractsActionsBase):
    ALLOW_LOCKED = True
    _allow_get_all = True


class RHAbstractsDownloadAttachments(AbstractsDownloadAttachmentsMixin, RHManageAbstractsExportActionsBase):
    pass


class RHAbstractsExportPDF(AbstractsExportPDFMixin, RHManageAbstractsExportActionsBase):
    pass


class RHAbstractsExportCSV(AbstractsExportCSV, RHManageAbstractsExportActionsBase):
    pass


class RHAbstractsExportExcel(AbstractsExportExcel, RHManageAbstractsExportActionsBase):
    pass


class RHAbstractsExportJSON(RHManageAbstractsExportActionsBase):
    _abstract_query_options = (joinedload('submitter'),
                               joinedload('accepted_track'),
                               joinedload('accepted_contrib_type'),
                               joinedload('submitted_contrib_type'),
                               subqueryload('comments'),
                               subqueryload('field_values'),
                               subqueryload('submitted_for_tracks'),
                               subqueryload('reviewed_for_tracks'),
                               subqueryload('person_links'),
                               subqueryload('reviews').joinedload('ratings').joinedload('question'))

    def _process(self):
        abstracts = abstracts_schema.dump(sorted(self.abstracts, key=attrgetter('friendly_id')))
        questions = abstract_review_questions_schema.dump(self.event.abstract_review_questions)
        response = jsonify(version=1, abstracts=abstracts, questions=questions)
        response.headers['Content-Disposition'] = 'attachment; filename="abstracts.json"'
        return response


class RHAbstractsAPIEmailAbstractRolesMetadata(EmailRolesMetadataMixin, RHManageAbstractsBase):
    object_context = 'abstracts'


class RHAbstractsAPIEmailAbstractRolesPreview(EmailRolesPreviewMixin, RHManageAbstractsActionsBase):
    object_context = 'abstracts'

    def get_placeholder_kwargs(self):
        abstract = self.abstracts[0]
        return {'person': abstract.submitter, 'abstract': abstract}


class RHAbstractsAPIEmailAbstractRolesSend(EmailRolesSendMixin, RHManageAbstractsActionsBase):
    object_context = 'abstracts'
    log_module = 'Abstracts'

    def get_recipients(self, roles):
        for abstract in self.abstracts:
            log_metadata = {'abstract_id': abstract.id}
            seen = set()
            if 'submitter' in roles:
                yield abstract.submitter.email, {'abstract': abstract, 'person': abstract.submitter}, log_metadata
                seen = {abstract.submitter.email, abstract.submitter}
            for person_link in abstract.person_links:
                if person_link.email in seen or person_link.person.user in seen or not person_link.email:
                    continue
                if self.get_roles_from_person_link(person_link) & roles:
                    yield person_link.email, {'abstract': abstract, 'person': person_link}, log_metadata
