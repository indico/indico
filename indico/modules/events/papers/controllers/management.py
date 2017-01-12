# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import request, render_template, flash, session

from indico.modules.events.contributions import Contribution
from indico.modules.events.papers import logger
from indico.modules.events.papers.controllers.base import RHManagePapersBase
from indico.modules.events.papers.forms import (BulkPaperJudgmentForm, make_competences_form, PapersScheduleForm,
                                                PaperTeamsForm, PaperReviewingSettingsForm)
from indico.modules.events.papers.lists import PaperAssignmentListGenerator
from indico.modules.events.papers.models.revisions import PaperRevisionState
from indico.modules.events.papers.operations import (set_reviewing_state, update_team_members, create_competences,
                                                     update_competences, judge_paper)
from indico.modules.events.papers.settings import paper_reviewing_settings, RoleConverter
from indico.modules.events.papers.views import WPManagePapers
from indico.modules.events.papers.operations import schedule_cfp, open_cfp, close_cfp
from indico.modules.users.models.users import User
from indico.util.i18n import _, ngettext
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


def _render_paper_dashboard(event, view_class=None):
    if view_class:
        return view_class.render_template('management/overview.html', event.as_legacy, event=event)
    else:
        return render_template('events/papers/management/overview.html', event=event)


class RHPapersDashboard(RHManagePapersBase):
    """Dashboard of the papers module"""

    # Allow access even if the feature is disabled
    EVENT_FEATURE = None

    def _process(self):
        if not self.event_new.has_feature('papers'):
            return WPManagePapers.render_template('management/disabled.html', self._conf, event=self.event_new)
        else:
            return _render_paper_dashboard(self.event_new, view_class=WPManagePapers)


class RHManagePaperTeams(RHManagePapersBase):
    """Modify managers of the papers module"""

    def _process(self):
        cfp = self.event_new.cfp
        form_data = {
            'managers': cfp.managers,
            'judges': cfp.judges,
            'content_reviewers': cfp.content_reviewers,
            'layout_reviewers': cfp.layout_reviewers
        }

        form = PaperTeamsForm(event=self.event_new, **form_data)
        if form.validate_on_submit():
            teams = {
                'managers': form.managers.data,
                'judges': form.judges.data
            }
            if cfp.content_reviewing_enabled:
                teams['content_reviewers'] = form.content_reviewers.data
            if cfp.layout_reviewing_enabled:
                teams['layout_reviewers'] = form.layout_reviewers.data
            update_team_members(self.event_new, **teams)
            flash(_("The members of the teams were updated successfully"), 'success')
            return jsonify_data()
        return jsonify_form(form)


class RHSwitchReviewingType(RHManagePapersBase):
    """Enable/disable the paper reviewing types"""

    def _process_PUT(self):
        set_reviewing_state(self.event_new, request.view_args['reviewing_type'], True)
        return jsonify_data(flash=False, html=_render_paper_dashboard(self.event_new))

    def _process_DELETE(self):
        set_reviewing_state(self.event_new, request.view_args['reviewing_type'], False)
        return jsonify_data(flash=False, html=_render_paper_dashboard(self.event_new))


class RHManageCompetences(RHManagePapersBase):
    """Manage the competences of the call for papers ACLs"""

    def _process(self):
        form_class = make_competences_form(self.event_new)
        user_competences = self.event_new.cfp.user_competences
        defaults = {'competences_{}'.format(user_id): competences.competences
                    for user_id, competences in user_competences.iteritems()}
        form = form_class(obj=FormDefaults(defaults))
        if form.validate_on_submit():
            key_prefix = 'competences_'
            form_data = {int(key[len(key_prefix):]): value for key, value in form.data.iteritems()}
            users = {u.id: u for u in User.query.filter(User.id.in_(form_data), ~User.is_deleted)}
            for user_id, competences in form_data.iteritems():
                if user_id in user_competences:
                    update_competences(user_competences[user_id], competences)
                elif competences:
                    create_competences(self.event_new, users[user_id], competences)
            flash(_("Team competences were updated successfully"), 'success')
            return jsonify_data()
        return WPManagePapers.render_template('management/competences.html', self._conf, event=self.event_new,
                                              form=form)


class RHScheduleCFP(RHManagePapersBase):
    def _process(self):
        form = PapersScheduleForm(obj=FormDefaults(**paper_reviewing_settings.get_all(self.event_new)),
                                  event=self.event_new)
        if form.validate_on_submit():
            rescheduled = self.event_new.cfp.start_dt is not None
            schedule_cfp(self.event_new, **form.data)
            if rescheduled:
                flash(_("Call for papers has been rescheduled"), 'success')
            else:
                flash(_("Call for papers has been scheduled"), 'success')
            return jsonify_data(html=_render_paper_dashboard(self.event_new))
        return jsonify_form(form)


class RHOpenCFP(RHManagePapersBase):
    """Open the call for papers"""

    def _process(self):
        open_cfp(self.event_new)
        flash(_("Call for papers is now open"), 'success')
        return jsonify_data(html=_render_paper_dashboard(self.event_new))


class RHCloseCFP(RHManagePapersBase):
    """Close the call for papers"""

    def _process(self):
        close_cfp(self.event_new)
        flash(_("Call for papers is now closed"), 'success')
        return jsonify_data(html=_render_paper_dashboard(self.event_new))


class RHPapersAssignmentList(RHManagePapersBase):
    """Assign contributions to reviewers and judges"""

    def _process(self):
        self.list_generator = PaperAssignmentListGenerator(event=self.event_new)
        return WPManagePapers.render_template('management/assignment.html', self._conf, event=self.event_new,
                                              **self.list_generator.get_list_kwargs())


class RHAssignmentListCustomize(RHManagePapersBase):
    """Filter options and columns to display for the paper assignment list of an event"""

    def _checkParams(self, params):
        RHManagePapersBase._checkParams(self, params)
        self.list_generator = PaperAssignmentListGenerator(event=self.event_new)

    def _process_GET(self):
        list_config = self.list_generator.list_config
        return WPManagePapers.render_template('management/assignment_list_filter.html', self._conf,
                                              event=self.event_new,
                                              static_items=self.list_generator.static_items,
                                              filters=list_config['filters'],
                                              visible_items=list_config['items'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())


class RHManagePapersActionsBase(RHManagePapersBase):
    """Base class for RHs performing actions on selected contributions"""

    _contrib_query_options = ()

    @property
    def _contrib_query(self):
        query = Contribution.query.with_parent(self.event_new)
        if self._contrib_query_options:
            query = query.options(*self._contrib_query_options)
        return query

    def _checkParams(self, params):
        RHManagePapersBase._checkParams(self, params)
        self.list_generator = PaperAssignmentListGenerator(event=self.event_new)
        ids = map(int, request.form.getlist('contribution_id'))
        self.contributions = self._contrib_query.filter(Contribution.id.in_(ids)).all()


class RHBulkPaperJudgment(RHManagePapersActionsBase):
    """Perform bulk change state operations on selected papers"""

    def _process(self):
        form = BulkPaperJudgmentForm(event=self.event_new, judgment=request.form.get('judgment'),
                                     contribution_id=[c.id for c in self.contributions])
        if form.validate_on_submit():
            judgment_data, contrib_data = form.split_data
            submitted_papers = [c for c in self.contributions if
                                c.paper_last_revision and c.paper_last_revision.state == PaperRevisionState.submitted]
            for submitted_paper in submitted_papers:
                judge_paper(submitted_paper, contrib_data, judge=session.user, **judgment_data)
            num_submitted_papers = len(submitted_papers)
            num_not_submitted_papers = len(self.contributions) - num_submitted_papers
            if num_submitted_papers:
                flash(ngettext("One paper has been judged.",
                               "{num} paper have been judged.",
                               num_submitted_papers).format(num=num_submitted_papers), 'success')
            if num_not_submitted_papers:
                flash(ngettext("One contribution has been skipped since it has no paper submitted yet or is in "
                               "a final state.",
                               "{num} contributions have been skipped since they have no paper submitted yet or are in "
                               "a final state.",
                               num_not_submitted_papers).format(num=num_not_submitted_papers), 'warning')
            return jsonify_data(**self.list_generator.render_list())
        return jsonify_form(form=form, submit=_('Judge'), disabled_until_change=False)


class RHManageReviewingSettings(RHManagePapersBase):
    def _process(self):
        defaults = FormDefaults(content_review_questions=self.event_new.cfp.content_review_questions,
                                layout_review_questions=self.event_new.cfp.layout_review_questions,
                                **paper_reviewing_settings.get_all(self.event_new))
        form = PaperReviewingSettingsForm(event=self.event_new, obj=defaults)
        if form.validate_on_submit():
            data = form.data
            content_review_questions = data.pop('content_review_questions', None)
            layout_review_questions = data.pop('layout_review_questions', None)
            if content_review_questions is None:
                content_review_questions = self.event_new.cfp.content_review_questions
            if layout_review_questions is None:
                layout_review_questions = self.event_new.cfp.layout_review_questions
            self.event_new.paper_review_questions = content_review_questions + layout_review_questions

            email_settings = data.pop('email_settings')
            data.update(email_settings)

            paper_reviewing_settings.set_multi(self.event_new, data)
            flash(_("The reviewing settings were saved successfully"), 'success')
            logger.info("Paper reviewing settings of %r updated by %r", self.event_new, session.user)
            return jsonify_data()
        self.commit = False
        return jsonify_form(form)
