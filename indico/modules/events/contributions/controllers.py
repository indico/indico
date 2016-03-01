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

from flask import flash, request, jsonify, redirect
from werkzeug.exceptions import BadRequest

from indico.modules.events.contributions.forms import ContributionForm, ContributionProtectionForm, SubContributionForm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.operations import (create_contribution, update_contribution,
                                                            delete_contribution, create_subcontribution,
                                                            update_subcontribution, delete_subcontribution)
from indico.modules.events.contributions.util import ContributionReporter
from indico.modules.events.contributions.views import WPManageContributions
from indico.modules.events.management.controllers import RHContributionPersonListMixin
from indico.modules.events.util import update_object_principals
from indico.util.i18n import _, ngettext
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


def _render_subcontribution_list(contrib):
    tpl = get_template_module('events/contributions/management/_subcontribution_list.html')
    return tpl.render_subcontribution_list(contrib.event_new, contrib)


class RHManageContributionsBase(RHConferenceModifBase):
    """Base class for all contributions management RHs"""
    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.reporter = ContributionReporter(event=self.event_new)

    def _process(self):
        return RH._process(self)


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


class RHManageSubContributionBase(RHManageContributionBase):
    """Base RH for a specific subcontribution"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.subcontrib
        }
    }

    def _checkParams(self, params):
        RHManageContributionBase._checkParams(self, params)
        self.subcontrib = SubContribution.get_one(request.view_args['subcontrib_id'], is_deleted=False)


class RHManageContributionsActionsBase(RHManageContributionsBase):
    """Base class for classes performing actions on event contributions"""

    def _checkParams(self, params):
        RHManageContributionsBase._checkParams(self, params)
        ids = {int(x) for x in request.form.getlist('contribution_id')}
        self.contribs = self.event_new.contributions.filter(Contribution.id.in_(ids)).all()


class RHManageSubContributionsActionsBase(RHManageContributionBase):
    """Base class for RHs performing actions on subcontributions"""

    def _checkParams(self, params):
        RHManageContributionBase._checkParams(self, params)
        ids = {int(x) for x in request.form.getlist('subcontribution_id')}
        self.subcontribs = (SubContribution.query
                            .with_parent(self.contrib)
                            .filter(SubContribution.id.in_(ids))
                            .all())


class RHContributions(RHManageContributionsBase):
    """Display contributions management page"""

    def _process(self):
        if self.reporter.static_link_used:
            return redirect(self.reporter.get_report_url())
        contrib_report_args = self.reporter.get_contrib_report_kwargs()
        return WPManageContributions.render_template('management/contributions.html', self._conf, event=self.event_new,
                                                     **contrib_report_args)


class RHContributionsReportCustomize(RHManageContributionsBase):
    """Filter options for the contributions report of an event"""

    def _process_GET(self):
        return WPManageContributions.render_template('management/contrib_report_filter.html', self._conf,
                                                     event=self.event_new,
                                                     filters=self.reporter.report_config['filters'],
                                                     filterable_items=self.reporter.filterable_items)

    def _process_POST(self):
        self.reporter.store_filters()
        return jsonify_data(**self.reporter.render_contrib_report())


class RHContributionsReportStaticURL(RHManageContributionsBase):
    """Generate a static URL for the configuration of the contribution report"""

    def _process(self):
        return jsonify(url=self.reporter.generate_static_url())


class RHCreateContribution(RHManageContributionsBase):
    def _process(self):
        inherited_location = self.event_new.location_data
        inherited_location['inheriting'] = True
        form = ContributionForm(event=self.event_new, obj=FormDefaults(location_data=inherited_location))
        if form.validate_on_submit():
            contrib = create_contribution(self.event_new, form.data)
            flash(_("Contribution '{}' created successfully").format(contrib.title), 'success')
            tpl_components = self.reporter.render_contrib_report(contrib)
            if tpl_components['hide_contrib']:
                self.reporter.flash_info_message(contrib)
            return jsonify_data(**tpl_components)
        return jsonify_template('events/contributions/forms/contribution.html', form=form)


class RHEditContribution(RHManageContributionBase):
    def _process(self):
        form = ContributionForm(obj=FormDefaults(self.contrib), event=self.event_new)
        if form.validate_on_submit():
            update_contribution(self.contrib, form.data)
            flash(_("Contribution '{}' successfully updated").format(self.contrib.title), 'success')
            tpl_components = self.reporter.render_contrib_report(self.contrib)
            if tpl_components['hide_contrib']:
                self.reporter.flash_info_message(self.contrib)
            return jsonify_data(**tpl_components)
        return jsonify_template('events/contributions/forms/contribution.html', form=form)


class RHDeleteContributions(RHManageContributionsActionsBase):
    def _process(self):
        for contrib in self.contribs:
            delete_contribution(contrib)
        deleted_count = len(self.contribs)
        flash(ngettext("The contribution has been deleted.",
                       "{count} contributions have been deleted.", deleted_count)
              .format(count=deleted_count), 'success')
        return jsonify_data(**self.reporter.render_contrib_report())


class RHContributionREST(RHManageContributionBase):
    def _process_DELETE(self):
        delete_contribution(self.contrib)
        flash(_("Contribution '{}' successfully deleted").format(self.contrib.title), 'success')
        return jsonify_data(**self.reporter.render_contrib_report())

    def _process_PATCH(self):
        data = request.json
        updates = {}
        if data.viewkeys() > {'session_id', 'track_id'}:
            raise BadRequest
        if 'session_id' in data:
            updates.update(self._get_contribution_session_updates(data['session_id']))
        if 'track_id' in data:
            updates.update(self._get_contribution_track_updates(data['track_id']))
        rv = {}
        if updates:
            rv = update_contribution(self.contrib, updates)
        return jsonify(unscheduled=rv.get('unscheduled', False), undo_unschedule=rv.get('undo_unschedule'))

    def _get_contribution_session_updates(self, session_id):
        updates = {}
        if session_id is None:
            updates['session'] = None
        else:
            session = self.event_new.sessions.filter_by(id=session_id).one()
            if not session:
                raise BadRequest('Invalid session id')
            if session != self.contrib.session:
                updates['session'] = session
        return updates

    def _get_contribution_track_updates(self, track_id):
        updates = {}
        if track_id is None:
            updates['track_id'] = None
        else:
            track = self._conf.getTrackById(str(track_id))
            if not track:
                raise BadRequest('Invalid track id')
            if track_id != self.contrib.track_id:
                updates['track_id'] = track_id
        return updates


class RHContributionPersonList(RHContributionPersonListMixin, RHManageContributionsActionsBase):
    """List of persons in the contribution"""

    @property
    def _membership_filter(self):
        contribution_ids = {contrib.id for contrib in self.contribs}
        return Contribution.id.in_(contribution_ids)


class RHContributionProtection(RHManageContributionBase):
    """Manage contribution protection"""

    def _process(self):
        form = ContributionProtectionForm(obj=FormDefaults(**self._get_defaults()), contrib=self.contrib)
        if form.validate_on_submit():
            update_contribution(self.contrib, {'protection_mode': form.protection_mode.data})
            update_object_principals(self.contrib, form.managers.data, full_access=True)
            if self.contrib.is_protected:
                update_object_principals(self.contrib, form.acl.data, read_access=True)
            update_object_principals(self.contrib, form.submitters.data, role='submit')
            return jsonify_data(flash=False, **self.reporter.render_contrib_report(self.contrib))
        return jsonify_form(form)

    def _get_defaults(self):
        managers = {p.principal for p in self.contrib.acl_entries if p.full_access}
        submitters = {p.principal for p in self.contrib.acl_entries if p.has_management_role('submit', explicit=True)}
        acl = {p.principal for p in self.contrib.acl_entries if p.read_access}
        return {'managers': managers, 'submitters': submitters, 'protection_mode': self.contrib.protection_mode,
                'acl': acl}


class RHContributionSubContributions(RHManageContributionBase):
    """Get a list of subcontributions"""

    def _process(self):
        return jsonify_data(html=_render_subcontribution_list(self.contrib))


class RHCreateSubContribution(RHManageContributionBase):
    """Create a subcontribution"""

    def _process(self):
        form = SubContributionForm(event=self.event_new)
        if form.validate_on_submit():
            subcontrib = create_subcontribution(self.contrib, form.data)
            flash(_("Subcontribution '{}' created successfully").format(subcontrib.title), 'success')
            return jsonify_data(html=_render_subcontribution_list(self.contrib))
        return jsonify_template('events/contributions/forms/contribution.html', form=form)


class RHEditSubContribution(RHManageSubContributionBase):
    """Edit the subcontribution"""

    def _process(self):
        form = SubContributionForm(obj=FormDefaults(self.subcontrib), event=self.event_new)
        if form.validate_on_submit():
            update_subcontribution(self.subcontrib, form.data)
            flash(_("Subcontribution '{}' updated successfully").format(self.subcontrib.title), 'success')
            return jsonify_data(html=_render_subcontribution_list(self.contrib))
        return jsonify_template('events/contributions/forms/contribution.html', form=form)


class RHSubContributionREST(RHManageSubContributionBase):
    """REST endpoint for management of a single subcontribution"""

    def _process_DELETE(self):
        delete_subcontribution(self.subcontrib)
        flash(_("Subcontribution '{}' deleted successfully").format(self.subcontrib.title), 'success')
        return jsonify_data(html=_render_subcontribution_list(self.contrib))


class RHDeleteSubContributions(RHManageSubContributionsActionsBase):
    def _process(self):
        for subcontrib in self.subcontribs:
            delete_subcontribution(subcontrib)
        return jsonify_data(html=_render_subcontribution_list(self.contrib))
