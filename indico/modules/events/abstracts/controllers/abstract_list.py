# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import defaultdict
from operator import attrgetter

from flask import flash, jsonify, request, session
from sqlalchemy.orm import joinedload, subqueryload

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
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.util import get_field_values
from indico.modules.users.models.users import User
from indico.util.i18n import _, ngettext
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHAbstractListBase(RHManageAbstractsBase):
    """Base class for all RHs using the abstract list generator."""

    def _process_args(self):
        RHManageAbstractsBase._process_args(self)
        self.list_generator = AbstractListGeneratorManagement(event=self.event)


class RHManageAbstractsActionsBase(RHAbstractListBase):
    """Base class for RHs performing actions on selected abstracts."""

    _abstract_query_options = ()

    @property
    def _abstract_query(self):
        query = Abstract.query.with_parent(self.event)
        if self._abstract_query_options:
            query = query.options(*self._abstract_query_options)
        return query

    def _process_args(self):
        RHAbstractListBase._process_args(self)
        ids = map(int, request.form.getlist('abstract_id'))
        self.abstracts = self._abstract_query.filter(Abstract.id.in_(ids)).all()


class RHBulkAbstractJudgment(RHManageAbstractsActionsBase):
    """Perform bulk judgment operations on selected abstracts."""

    def _process(self):
        form = BulkAbstractJudgmentForm(event=self.event, abstract_id=[a.id for a in self.abstracts],
                                        judgment=request.form.get('judgment'))
        if form.validate_on_submit():
            judgment_data, abstract_data = form.split_data
            submitted_abstracts = {abstract for abstract in self.abstracts if abstract.state == AbstractState.submitted}
            for abstract in submitted_abstracts:
                judge_abstract(abstract, abstract_data, judge=session.user, **judgment_data)
            num_judged_abstracts = len(submitted_abstracts)
            num_prejudged_abstracts = len(self.abstracts) - num_judged_abstracts
            if num_judged_abstracts:
                flash(ngettext("One abstract has been judged.",
                               "{num} abstracts have been judged.",
                               num_judged_abstracts).format(num=num_judged_abstracts), 'success')
            if num_prejudged_abstracts:
                flash(ngettext("One abstract has been skipped since it is already judged.",
                               "{num} abstracts have been skipped since they are already judged.",
                               num_prejudged_abstracts).format(num=num_prejudged_abstracts), 'warning')
            return jsonify_data(**self.list_generator.render_list())
        return jsonify_form(form=form, fields=form._order, submit=_('Judge'), disabled_until_change=False)


class RHAbstractList(DisplayAbstractListMixin, RHAbstractListBase):
    template = 'management/abstract_list.html'
    view_class = WPManageAbstracts

    def _render_template(self, **kwargs):
        kwargs['track_session_map'] = {track.id: track.default_session_id for track in self.event.tracks}
        can_create = can_create_invited_abstracts(self.event)
        return super(RHAbstractList, self)._render_template(can_create_invited_abstracts=can_create, **kwargs)


class RHAbstractListCustomize(CustomizeAbstractListMixin, RHAbstractListBase):
    view_class = WPManageAbstracts
    ALLOW_LOCKED = True


class RHAbstractListStaticURL(RHAbstractListBase):
    """Generate a static URL for the configuration of the abstract list."""

    ALLOW_LOCKED = True

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHCreateAbstract(RHAbstractListBase):
    def _process(self):
        is_invited = request.args.get('invited') == '1'
        abstract_form_class = make_abstract_form(self.event, session.user, notification_option=True,
                                                 management=self.management, invited=is_invited)
        form = abstract_form_class(event=self.event, management=self.management, invited=is_invited)
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
            abstract = create_abstract(self.event, *get_field_values(data), send_notifications=send_notifications,
                                       submitter=submitter, is_invited=is_invited)
            flash(_("Abstract '{}' created successfully").format(abstract.title), 'success')
            tpl_components = self.list_generator.render_list(abstract)
            if tpl_components.get('hide_abstract'):
                self.list_generator.flash_info_message(abstract)
            return jsonify_data(**tpl_components)
        return jsonify_form(form, back=_("Cancel"), form_header_kwargs={'action': request.relative_url})


class RHDeleteAbstracts(RHManageAbstractsActionsBase):
    def _process(self):
        delete_contribs = request.values.get('delete_contribs') == '1'
        deleted_contrib_count = 0
        for abstract in self.abstracts:
            if delete_contribs and abstract.contribution:
                deleted_contrib_count += 1
            delete_abstract(abstract, delete_contribs)
        deleted_abstract_count = len(self.abstracts)
        flash(ngettext("The abstract has been deleted.",
                       "{count} abstracts have been deleted.", deleted_abstract_count)
              .format(count=deleted_abstract_count), 'success')
        if deleted_contrib_count:
            flash(ngettext("The linked contribution has been deleted.",
                           "{count} linked contributions have been deleted.", deleted_contrib_count)
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
        submitters = {abstract.submitter for abstract in self.abstracts}
        abstract_persons = AbstractPersonLink.find_all(AbstractPersonLink.abstract.has(self._membership_filter))
        abstract_persons_dict = defaultdict(lambda: {'speaker': False, 'submitter': False, 'primary_author': False,
                                                     'secondary_author': False})
        for abstract_person in abstract_persons:
            dict_key = abstract_person.person.user if abstract_person.person.user else abstract_person.person
            person_roles = abstract_persons_dict[dict_key]
            person_roles['speaker'] |= abstract_person.is_speaker
            person_roles['primary_author'] |= abstract_person.author_type == AuthorType.primary
            person_roles['secondary_author'] |= abstract_person.author_type == AuthorType.secondary
        for submitter in submitters:
            abstract_persons_dict[submitter]['submitter'] |= True
        return jsonify_template('events/abstracts/management/abstract_person_list.html',
                                event_persons=abstract_persons_dict, event=self.event)


class RHManageAbstractsExportActionsBase(RHManageAbstractsActionsBase):
    ALLOW_LOCKED = True


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
