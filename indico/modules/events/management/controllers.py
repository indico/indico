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

from flask import flash, redirect, session, request
from markupsafe import Markup
from werkzeug.exceptions import Forbidden, NotFound, BadRequest

from indico.core.db.sqlalchemy.protection import render_acl, ProtectionMode
from indico.modules.categories.models.categories import Category
from indico.modules.events import EventLogRealm, EventLogKind
from indico.modules.events.contributions.models.persons import (ContributionPersonLink, SubContributionPersonLink,
                                                                AuthorType)
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.forms import EventReferencesForm, EventLocationForm, EventPersonLinkForm, EventKeywordsForm
from indico.modules.events.management.forms import EventProtectionForm
from indico.modules.events.management.util import flash_if_unregistered, can_lock
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.operations import delete_event, create_event_references, update_event
from indico.modules.events.sessions import session_settings, COORDINATOR_PRIV_SETTINGS, COORDINATOR_PRIV_TITLES
from indico.modules.events.util import get_object_from_args, update_object_principals
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template, jsonify_data, jsonify_form
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHDeleteEvent(RHConferenceModifBase):
    """Delete an event."""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)

    def _process_GET(self):
        return jsonify_template('events/management/delete_event.html', event=self.event_new)

    def _process_POST(self):
        delete_event(self.event_new)
        flash(_('Event "{}" successfully deleted.').format(self.event_new.title), 'success')
        category = self.event_new.category
        endpoint = 'categories.manage_content' if category.can_manage(session.user) else 'categories.display'
        redirect_url = url_for(endpoint, category)
        return jsonify_data(url=redirect_url, flash=False)


class RHLockEvent(RHConferenceModifBase):
    """Lock an event."""

    CSRF_ENABLED = True

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        if not can_lock(self.event_new, session.user):
            raise Forbidden

    def _process(self):
        return RH._process(self)

    def _process_GET(self):
        return jsonify_template('events/management/lock_event.html')

    def _process_POST(self):
        self._conf.setClosed(True)
        flash(_('The event is now locked.'), 'success')
        return jsonify_data(url=url_for('event_mgmt.conferenceModification', self.event_new), flash=False)


class RHUnlockEvent(RHConferenceModifBase):
    """Unlock an event."""

    CSRF_ENABLED = True

    def _checkProtection(self):
        self._allowClosed = can_lock(self.event_new, session.user)
        RHConferenceModifBase._checkProtection(self)

    def _process(self):
        self._conf.setClosed(False)
        flash(_('The event is now unlocked.'), 'success')
        return redirect(url_for('event_mgmt.conferenceModification', self.event_new))


class RHContributionPersonListMixin:
    """List of persons somehow related to contributions (co-authors, speakers...)"""

    @property
    def _membership_filter(self):
        raise NotImplementedError

    def _process(self):
        contribution_persons = (ContributionPersonLink
                                .find(ContributionPersonLink.contribution.has(self._membership_filter))
                                .all())
        contribution_persons.extend(SubContributionPersonLink
                                    .find(SubContributionPersonLink.subcontribution
                                          .has(SubContribution.contribution.has(self._membership_filter)))
                                    .all())

        contribution_persons_dict = defaultdict(lambda: {'speaker': False, 'primary_author': False,
                                                         'secondary_author': False})
        for contrib_person in contribution_persons:
            person_roles = contribution_persons_dict[contrib_person.person]
            person_roles['speaker'] |= contrib_person.is_speaker
            person_roles['primary_author'] |= contrib_person.author_type == AuthorType.primary
            person_roles['secondary_author'] |= contrib_person.author_type == AuthorType.secondary
        return jsonify_template('events/management/contribution_person_list.html',
                                event_persons=contribution_persons_dict, event=self.event_new)


class RHShowNonInheriting(RHConferenceModifBase):
    """Show a list of non-inheriting child objects"""

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.obj = get_object_from_args()[2]
        if self.obj is None:
            raise NotFound

    def _process(self):
        objects = self.obj.get_non_inheriting_objects()
        return jsonify_template('events/management/non_inheriting_objects.html', objects=objects)


class RHEventACL(RHConferenceModifBase):
    """Display the inherited ACL of the event"""

    def _process(self):
        return render_acl(self.event_new)


class RHEventACLMessage(RHConferenceModifBase):
    """Render the inheriting ACL message"""

    def _process(self):
        mode = ProtectionMode[request.args['mode']]
        return jsonify_template('forms/protection_field_acl_message.html', object=self.event_new, mode=mode,
                                endpoint='event_management.acl')


class RHEventProtection(RHConferenceModifBase):
    """Show event protection"""

    def _process(self):
        form = EventProtectionForm(obj=FormDefaults(**self._get_defaults()), event=self.event_new)
        if form.validate_on_submit():
            update_event(self.event_new, {'protection_mode': form.protection_mode.data,
                                          'own_no_access_contact': form.own_no_access_contact.data,
                                          'access_key': form.access_key.data})
            update_object_principals(self.event_new, form.acl.data, read_access=True)
            update_object_principals(self.event_new, form.managers.data, full_access=True)
            update_object_principals(self.event_new, form.submitters.data, role='submit')
            self._update_session_coordinator_privs(form)
            flash(_('Protection settings have been updated'), 'success')
            return redirect(url_for('.protection', self.event_new))
        return WPEventManagement.render_template('event_protection.html', self._conf, form=form, event=self.event_new)

    def _get_defaults(self):
        acl = {p.principal for p in self.event_new.acl_entries if p.read_access}
        submitters = {p.principal for p in self.event_new.acl_entries if p.has_management_role('submit', explicit=True)}
        managers = {p.principal for p in self.event_new.acl_entries if p.full_access}
        registration_managers = {p.principal for p in self.event_new.acl_entries
                                 if p.has_management_role('registration', explicit=True)}
        event_session_settings = session_settings.get_all(self.event_new)
        coordinator_privs = {name: event_session_settings[val] for name, val in COORDINATOR_PRIV_SETTINGS.iteritems()
                             if event_session_settings.get(val)}
        return dict({'protection_mode': self.event_new.protection_mode, 'acl': acl, 'managers': managers,
                     'registration_managers': registration_managers, 'submitters': submitters,
                     'access_key': self.event_new.access_key,
                     'own_no_access_contact': self.event_new.own_no_access_contact}, **coordinator_privs)

    def _update_session_coordinator_privs(self, form):
        for priv_field in form.priv_fields:
            try:
                setting = COORDINATOR_PRIV_SETTINGS[priv_field]
            except KeyError:
                raise BadRequest('No such privilege')
            if session_settings.get(self.event_new, setting) == form.data[priv_field]:
                continue
            session_settings.set(self.event_new, setting, form.data[priv_field])
            log_msg = 'Session coordinator privilege changed to {}: {}'.format(form.data[priv_field],
                                                                               COORDINATOR_PRIV_TITLES[priv_field])
            self.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Protection', log_msg, session.user)


class RHMoveEvent(RHConferenceModifBase):
    """Move event to a different category"""

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.target_category = Category.get_one(int(request.form['target_category_id']), is_deleted=False)
        if not self.target_category.can_create_events(session.user):
            raise Forbidden(_("You may only move events to categories where you are allowed to create events."))

    def _process(self):
        sep = ' \N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK} '
        old_path = sep.join(self.event_new.category.chain_titles)
        new_path = sep.join(self.target_category.chain_titles)
        self.event_new.move(self.target_category)
        self.event_new.log(EventLogRealm.management, EventLogKind.change, 'Category', 'Event moved', session.user,
                           data={'From': old_path, 'To': new_path})
        flash(_('Event "{}" has been moved to category "{}"').format(self.event_new.title, self.target_category.title),
              'success')
        return jsonify_data(flash=False)


class RHManageReferences(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _process(self):
        form = EventReferencesForm(obj=FormDefaults(references=self.event_new.references))
        if form.validate_on_submit():
            create_event_references(event=self.event_new, data=form.data)
            flash(_('External IDs saved'), 'success')
            tpl = get_template_module('events/management/_reference_list.html')
            return jsonify_data(html=tpl.render_event_references_list(self.event_new.references))
        return jsonify_form(form)


class RHManageEventLocation(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _process(self):
        form = EventLocationForm(obj=self.event_new)
        if form.validate_on_submit():
            update_event(self.event_new, form.data)
            flash(_('The location for the event has been updated'))
            tpl = get_template_module('events/management/_event_location.html')
            return jsonify_data(html=tpl.render_event_location_info(self.event_new.location_data))
        return jsonify_form(form)


class RHManageEventKeywords(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _process(self):
        form = EventKeywordsForm(obj=self.event_new)
        if form.validate_on_submit():
            update_event(self.event_new, form.data)
            flash(_('The keywords for the event have been updated'))
            return jsonify_data(html=Markup('<br>').join(self.event_new.keywords))
        return jsonify_form(form)


class RHManageEventPersonLinks(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _process(self):
        form = EventPersonLinkForm(obj=self.event_new, event=self.event_new, event_type=self.event_new.type)
        if form.validate_on_submit():
            with flash_if_unregistered(self.event_new, lambda: self.event_new.person_links):
                update_event(self.event_new, form.data)
            tpl = get_template_module('events/management/_event_person_links.html')
            return jsonify_data(html=tpl.render_event_person_links(self.event_new.type, self.event_new.person_links))
        self.commit = False
        return jsonify_form(form)
