# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from collections import defaultdict
from itertools import chain
from operator import attrgetter

from flask import flash, jsonify, request, session
from sqlalchemy.orm import selectinload, subqueryload
from werkzeug.exceptions import Forbidden
from werkzeug.utils import cached_property

from indico.modules.events.contributions import Contribution
from indico.modules.events.papers.controllers.base import RHJudgingAreaBase
from indico.modules.events.papers.forms import BulkPaperJudgmentForm
from indico.modules.events.papers.lists import PaperAssignmentListGenerator, PaperJudgingAreaListGeneratorDisplay
from indico.modules.events.papers.models.revisions import PaperRevisionState
from indico.modules.events.papers.operations import judge_paper, update_reviewing_roles
from indico.modules.events.papers.schemas import CallForPapersSchema, PaperDumpSchema
from indico.modules.events.papers.settings import PaperReviewingRole
from indico.modules.events.papers.views import WPDisplayJudgingArea, WPManagePapers
from indico.modules.events.util import ZipGeneratorMixin
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


CFP_ROLE_MAP = {
    PaperReviewingRole.judge: attrgetter('judges'),
    PaperReviewingRole.content_reviewer: attrgetter('content_reviewers'),
    PaperReviewingRole.layout_reviewer: attrgetter('layout_reviewers'),
}

CONTRIB_ROLE_MAP = {
    PaperReviewingRole.judge: attrgetter('paper_judges'),
    PaperReviewingRole.content_reviewer: attrgetter('paper_content_reviewers'),
    PaperReviewingRole.layout_reviewer: attrgetter('paper_layout_reviewers'),
}


class RHPapersListBase(RHJudgingAreaBase):
    """Base class for assignment/judging paper lists."""

    @cached_property
    def list_generator(self):
        if self.management:
            return PaperAssignmentListGenerator(event=self.event)
        else:
            return PaperJudgingAreaListGeneratorDisplay(event=self.event, user=session.user)


class RHPapersList(RHPapersListBase):
    """Display the paper list for assignment/judging."""

    @cached_property
    def view_class(self):
        return WPManagePapers if self.management else WPDisplayJudgingArea

    def _process(self):
        return self.view_class.render_template(self.template, self.event, **self.list_generator.get_list_kwargs())

    @cached_property
    def template(self):
        return 'management/assignment.html' if self.management else 'display/judging_area.html'


class RHCustomizePapersList(RHPapersListBase):
    """Filter options and columns to display for the paper list."""

    ALLOW_LOCKED = True

    def _process_GET(self):
        list_config = self.list_generator.list_config
        return jsonify_template('events/papers/paper_list_filter.html',
                                event=self.event,
                                static_items=self.list_generator.static_items,
                                filters=list_config['filters'],
                                visible_items=list_config['items'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())


class RHPapersActionBase(RHPapersListBase):
    """Base class for actions on selected papers."""

    def _get_contrib_query_options(self):
        return ()

    def _process_args(self):
        RHPapersListBase._process_args(self)
        ids = request.form.getlist('contribution_id', type=int)
        self.contributions = (self.list_generator._build_query()
                              .filter(Contribution.id.in_(ids))
                              .options(*self._get_contrib_query_options())
                              .all())


class RHDownloadPapers(ZipGeneratorMixin, RHPapersActionBase):
    """
    Generate a ZIP file with paper files for a given list of contributions.
    """

    ALLOW_LOCKED = True

    def _prepare_folder_structure(self, item):
        paper_title = secure_filename('{}_{}'.format(item.paper.contribution.friendly_id,
                                                     item.paper.contribution.title), 'paper')
        file_name = secure_filename(f'{item.id}_{item.filename}', 'paper')
        return os.path.join(*self._adjust_path_length([paper_title, file_name]))

    def _iter_items(self, contributions):
        contributions_with_paper = [c for c in contributions if c.paper]
        for contrib in contributions_with_paper:
            yield from contrib.paper.last_revision.files

    def _process(self):
        return self._generate_zip_file(self.contributions, name_prefix='paper-files', name_suffix=self.event.id)


class RHExportPapersJSON(RHPapersActionBase):
    """Generate a JSON file with all the paper details."""

    ALLOW_LOCKED = True

    def _check_access(self):
        RHPapersActionBase._check_access(self)
        if not self.management:
            raise Forbidden

    def _get_contrib_query_options(self):
        revisions_strategy = subqueryload('_paper_revisions')
        revisions_strategy.subqueryload('comments').joinedload('user')
        revisions_strategy.subqueryload('files')
        reviews_strategy = revisions_strategy.subqueryload('reviews')
        reviews_strategy.joinedload('user')
        ratings_strategy = reviews_strategy.subqueryload('ratings')
        ratings_strategy.joinedload('question')
        revisions_strategy.joinedload('submitter')
        revisions_strategy.joinedload('judge')
        return (revisions_strategy,)

    def _process(self):
        papers = [c.paper for c in self.contributions if c.paper]
        cfp_dump = CallForPapersSchema().dump(self.event.cfp)
        papers_dump = PaperDumpSchema(many=True).dump(papers)
        response = jsonify(version=1, papers=papers_dump, **cfp_dump)
        response.headers['Content-Disposition'] = 'attachment; filename="papers.json"'
        return response


class RHJudgePapers(RHPapersActionBase):
    """Bulk judgment of papers."""

    def _process(self):
        form = BulkPaperJudgmentForm(event=self.event, judgment=request.form.get('judgment'),
                                     contribution_id=[c.id for c in self.contributions])
        if form.validate_on_submit():
            submitted_papers = [c.paper for c in self.contributions if
                                c.paper and c.paper.last_revision.state == PaperRevisionState.submitted]
            for submitted_paper in submitted_papers:
                judge_paper(submitted_paper, form.judgment.data, form.judgment_comment.data, judge=session.user)
            num_submitted_papers = len(submitted_papers)
            num_not_submitted_papers = len(self.contributions) - num_submitted_papers
            if num_submitted_papers:
                flash(ngettext('One paper has been judged.',
                               '{num} papers have been judged.',
                               num_submitted_papers).format(num=num_submitted_papers), 'success')
            if num_not_submitted_papers:
                flash(ngettext('One contribution has been skipped since it has no paper submitted yet or it is in '
                               'a final state.',
                               '{num} contributions have been skipped since they have no paper submitted yet or they '
                               'are in a final state.',
                               num_not_submitted_papers).format(num=num_not_submitted_papers), 'warning')
            return jsonify_data(**self.list_generator.render_list())
        return jsonify_form(form=form, submit=_('Judge'), disabled_until_change=False)


class RHAssignPapersBase(RHPapersActionBase):
    """Base class for assigning/unassigning paper reviewing roles."""

    def _get_contrib_query_options(self):
        return [selectinload('person_links')]

    def _process_args(self):
        RHPapersActionBase._process_args(self)
        self.role = PaperReviewingRole[request.view_args['role']]
        user_ids = request.form.getlist('user_id', type=int)
        self.users = {u for u in CFP_ROLE_MAP[self.role](self.event.cfp) if u.id in user_ids}

    def _check_access(self):
        RHPapersActionBase._check_access(self)
        if not self.management and self.role == PaperReviewingRole.judge:
            raise Forbidden

    def _process_assignment(self, assign):
        update_reviewing_roles(self.event, self.users, self.contributions, self.role, assign)
        if assign:
            flash(_('Paper reviewing roles have been assigned.'), 'success')
        else:
            flash(_('Paper reviewing roles have been unassigned.'), 'success')
        return jsonify_data(**self.list_generator.render_list())

    def _get_conflicts(self, users):
        conflicts = defaultdict(list)
        for user in users:
            if not user.affiliation:
                continue
            for contribution in self.contributions:
                conflicts[user].extend(
                    (
                        contribution.title,
                        url_for('contributions.display_contribution', contribution),
                    )
                    for person in contribution.person_links
                    if user.affiliation in person.affiliation
                )
        return conflicts

    def _render_form(self, users, action):
        conflicts = self._get_conflicts(users)
        user_competences = self.event.cfp.user_competences
        competences = {f'competences_{user_id}': competences.competences
                       for user_id, competences in user_competences.items()}
        return jsonify_template('events/papers/assign_role.html', event=self.event, role=self.role.name,
                                action=action, users=users, competences=competences,
                                contribs=self.contributions, conflicts=conflicts)


class RHAssignPapers(RHAssignPapersBase):
    """Render the user list to assign paper reviewing roles."""

    def _process(self):
        if self.users:
            return self._process_assignment(True)
        users = CFP_ROLE_MAP[self.role](self.event.cfp)
        return self._render_form(users, 'assign')


class RHUnassignPapers(RHAssignPapersBase):
    """Render the user list to unassign paper reviewing roles."""

    def _process(self):
        if self.users:
            return self._process_assignment(False)
        _get_users = CONTRIB_ROLE_MAP[self.role]
        users = set(chain.from_iterable(_get_users(c) for c in self.contributions))
        return self._render_form(users, 'unassign')
