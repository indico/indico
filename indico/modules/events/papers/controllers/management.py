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

from collections import defaultdict

from flask import flash, render_template, request, session

from indico.modules.events.papers import logger
from indico.modules.events.papers.controllers.base import RHManagePapersBase
from indico.modules.events.papers.forms import (DeadlineForm, PaperReviewingSettingsForm, PapersScheduleForm,
                                                PaperTeamsForm, make_competences_form)
from indico.modules.events.papers.models.reviews import PaperReviewType
from indico.modules.events.papers.operations import (close_cfp, create_competences, open_cfp, schedule_cfp,
                                                     set_deadline, set_reviewing_state, update_competences,
                                                     update_team_members)
from indico.modules.events.papers.settings import PaperReviewingRole, paper_reviewing_settings
from indico.modules.events.papers.views import WPManagePapers
from indico.modules.users.models.users import User
from indico.util.i18n import _, ngettext
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


def _render_paper_dashboard(event, view_class=None):
    if view_class:
        return view_class.render_template('management/overview.html', event)
    else:
        return render_template('events/papers/management/overview.html', event=event, standalone=True)


class RHPapersDashboard(RHManagePapersBase):
    """Dashboard of the papers module"""

    # Allow access even if the feature is disabled
    EVENT_FEATURE = None

    def _process(self):
        if not self.event_new.has_feature('papers'):
            return WPManagePapers.render_template('management/disabled.html', self.event_new)
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
            unassigned_contribs = update_team_members(self.event_new, **teams)
            flash(_("The members of the teams were updated successfully"), 'success')
            if unassigned_contribs:
                flash(ngettext("Users have been removed from 1 contribution",
                               "Users have been removed from {} contributions",
                               len(unassigned_contribs)).format(len(unassigned_contribs)),
                      'warning')
            return jsonify_data()
        return jsonify_template('events/papers/management/teams.html', form=form)


class RHSwitchReviewingType(RHManagePapersBase):
    """Enable/disable the paper reviewing types"""

    def _process_PUT(self):
        set_reviewing_state(self.event_new, PaperReviewType[request.view_args['reviewing_type']], True)
        return jsonify_data(flash=False, html=_render_paper_dashboard(self.event_new))

    def _process_DELETE(self):
        set_reviewing_state(self.event_new, PaperReviewType[request.view_args['reviewing_type']], False)
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
        return jsonify_template('events/papers/management/competences.html', event=self.event_new, form=form)


class RHContactStaff(RHManagePapersBase):
    """Send emails to reviewing staff"""

    def _process(self):
        paper_persons_dict = {}
        for p in self.event_new.acl_entries:
            user = p.principal
            is_judge = p.has_management_role('paper_judge', explicit=True)
            is_content_reviewer = (self.event_new.cfp.content_reviewing_enabled and
                                   p.has_management_role('paper_content_reviewer', explicit=True))
            is_layout_reviewer = (self.event_new.cfp.layout_reviewing_enabled and
                                  p.has_management_role('paper_layout_reviewer', explicit=True))
            if is_judge or is_content_reviewer or is_layout_reviewer:
                paper_persons_dict[user] = {'judge': is_judge, 'content_reviewer': is_content_reviewer,
                                            'layout_reviewer': is_layout_reviewer}
        return jsonify_template('events/papers/management/paper_person_list.html',
                                event_persons=paper_persons_dict, event=self.event_new)


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


class RHSetDeadline(RHManagePapersBase):
    def _process(self):
        role = PaperReviewingRole[request.view_args['role']]
        deadline = paper_reviewing_settings.get(self.event_new, '{}_deadline'.format(role.name))
        enforce = paper_reviewing_settings.get(self.event_new, 'enforce_{}_deadline'.format(role.name))
        form = DeadlineForm(obj=FormDefaults(deadline=deadline, enforce=enforce), event=self.event_new)
        if form.validate_on_submit():
            set_deadline(self.event_new, role, form.deadline.data, form.enforce.data)
            messages = {
                PaperReviewingRole.content_reviewer: _('Content reviewing deadline has been set.'),
                PaperReviewingRole.layout_reviewer: _('Layout reviewing deadline has been set.'),
                PaperReviewingRole.judge: _('Judging deadline has been set.')
            }
            flash(messages[role], 'success')
            return jsonify_data(html=_render_paper_dashboard(self.event_new))
        return jsonify_form(form)
