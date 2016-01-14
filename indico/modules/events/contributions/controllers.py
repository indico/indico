# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import flash, request
from sqlalchemy.orm import joinedload

from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.operations import create_contribution, update_contribution, delete_contribution
from indico.modules.events.contributions.forms import ContributionForm
from indico.modules.events.contributions.views import WPManageContributions
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form
from indico.util.i18n import _, ngettext
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


def _get_contribution_list_args(event):
    timetable_entry_strategy = joinedload('timetable_entry')
    timetable_entry_strategy.lazyload('*')
    contribs = (event.contributions
                .filter_by(is_deleted=False)
                .order_by(Contribution.id)
                .options(timetable_entry_strategy)
                .all())
    sessions = event.sessions.filter_by(is_deleted=False).all()
    tracks = event.as_legacy.getTrackList()
    return {'contribs': contribs, 'sessions': sessions, 'tracks': tracks}


def _render_contribution_list(event):
    tpl = get_template_module('events/contributions/management/_contribution_list.html')
    return tpl.render_contribution_list(**_get_contribution_list_args(event))


class RHManageContributionsBase(RHConferenceModifBase):
    """Base class for all contributions management RHs"""

    CSRF_ENABLED = True


class RHManageContributionBase(RHManageContributionsBase):
    """Base class for a specific contribution"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        }
    }

    def _checkParams(self, params):
        RHManageContributionsBase._checkParams(self, params)
        self.contrib = Contribution.find_one(id=request.view_args['contrib_id'], is_deleted=False)


class RHManageContributionsActionsBase(RHManageContributionsBase):
    """Base class for classes performing actions on registrations"""

    def _checkParams(self, params):
        RHManageContributionsBase._checkParams(self, params)
        ids = set(map(int, request.form.getlist('contribution_id')))
        self.contribs = self.event_new.contributions.filter(Contribution.id.in_(ids), ~Contribution.is_deleted).all()


class RHContributions(RHManageContributionsBase):
    """Display contributions management page"""

    def _process(self):
        return WPManageContributions.render_template('management/contributions.html', self._conf, event=self.event_new,
                                                     **_get_contribution_list_args(self.event_new))


class RHCreateContribution(RHManageContributionsBase):
    def _process(self):
        form = ContributionForm()
        if form.validate_on_submit():
            contrib = create_contribution(self.event_new, form.data)
            flash(_("Contribution '{}' created successfully").format(contrib.title), 'success')
            return jsonify_data(html=_render_contribution_list(self.event_new))
        return jsonify_form(form)


class RHEditContribution(RHManageContributionBase):
    def _process(self):
        form = ContributionForm(obj=FormDefaults(self.contrib))
        if form.validate_on_submit():
            update_contribution(self.contrib, form.data)
            flash(_("Contribution '{}' successfully updated").format(self.contrib), 'success')
            return jsonify_data(html=_render_contribution_list(self.event_new))
        return jsonify_form(form)


class RHDeleteContribution(RHManageContributionBase):
    def _process(self):
        delete_contribution(self.contrib)
        flash(_("Contribution '{}' successfully deleted").format(self.contrib), 'success')
        return jsonify_data(html=_render_contribution_list(self.event_new))


class RHDeleteContributions(RHManageContributionsActionsBase):
    def _process(self):
        for contrib in self.contribs:
            delete_contribution(contrib)
        deleted_count = len(self.contribs)
        flash(ngettext("The contribution has been deleted.",
                       "{count} contributions have been deleted.", deleted_count)
              .format(count=deleted_count), 'success')
        return jsonify_data(html=_render_contribution_list(self.event_new))
