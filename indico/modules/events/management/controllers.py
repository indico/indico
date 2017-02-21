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

import uuid
from collections import defaultdict

from flask import flash, redirect, session, request, signals
from werkzeug.exceptions import Forbidden, NotFound

from indico.core import signals
from indico.core.db.sqlalchemy.protection import render_acl, ProtectionMode
from indico.modules.categories.models.categories import Category
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.events import EventLogRealm, EventLogKind
from indico.modules.events.contributions.models.persons import (ContributionPersonLink, SubContributionPersonLink,
                                                                AuthorType)
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.management.forms import (EventProtectionForm, EventDataForm, EventDatesForm,
                                                    EventLocationForm, EventPersonsForm, EventContactInfoForm,
                                                    EventClassificationForm, PosterPrintingForm)
from indico.modules.events.management.util import can_lock, flash_if_unregistered
from indico.modules.events.management.views import WPEventSettings, WPEventProtection
from indico.modules.events.models.events import EventType
from indico.modules.events.operations import (delete_event, update_event_protection, update_event, update_event_type,
                                              lock_event, unlock_event)
from indico.modules.events.posters import PosterPDF
from indico.modules.events.sessions import session_settings, COORDINATOR_PRIV_SETTINGS
from indico.modules.events.sessions.operations import update_session_coordinator_privs
from indico.modules.events.util import get_object_from_args, update_object_principals, track_time_changes
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for, send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template, jsonify_data, jsonify_form, url_for_index
from MaKaC.common.cache import GenericCache
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


poster_cache = GenericCache('poster-printing')


class RHManageEventBase(RHConferenceModifBase):
    """Base class for event management RHs"""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)


class RHEventSettings(RHManageEventBase):
    """Event settings dashboard"""

    def _checkProtection(self):
        if not session.user:
            raise Forbidden
        # If the user cannot manage the whole event see if anything gives them
        # limited management access.
        if not self.event_new.can_manage(session.user):
            urls = sorted(values_from_signal(signals.event_management.management_url.send(self.event_new),
                                             single_value=True))
            response = redirect(urls[0]) if urls else None
            raise Forbidden(response=response)

    def _process(self):
        return WPEventSettings.render_template('settings.html', self._conf, event=self.event_new)


class RHEditEventDataBase(RHManageEventBase):
    form_class = None

    def render_form(self, form):
        return jsonify_form(form)

    def render_settings_box(self):
        tpl = get_template_module('events/management/_settings.html')
        return tpl.render_event_settings(self.event_new)

    def _process(self):
        form = self.form_class(obj=self.event_new, event=self.event_new)
        if form.validate_on_submit():
            with flash_if_unregistered(self.event_new, lambda: self.event_new.person_links):
                update_event(self.event_new, **form.data)
            return jsonify_data(flash=False, html=self.render_settings_box())
        self.commit = False
        return self.render_form(form)


class RHEditEventData(RHEditEventDataBase):
    form_class = EventDataForm


class RHEditEventLocation(RHEditEventDataBase):
    form_class = EventLocationForm


class RHEditEventPersons(RHEditEventDataBase):
    form_class = EventPersonsForm


class RHEditEventContactInfo(RHEditEventDataBase):
    form_class = EventContactInfoForm

    def render_form(self, form):
        return jsonify_template('events/management/event_contact_info.html', form=form)


class RHEditEventClassification(RHEditEventDataBase):
    form_class = EventClassificationForm


class RHEditEventDates(RHManageEventBase):
    def _process(self):
        defaults = FormDefaults(self.event_new, update_timetable=True)
        form = EventDatesForm(obj=defaults, event=self.event_new)
        if form.validate_on_submit():
            with track_time_changes():
                update_event(self.event_new, **form.data)
            return jsonify_data(flash=False)
        show_screen_dates = form.has_displayed_dates and (form.start_dt_override.data or form.end_dt_override.data)
        return jsonify_template('events/management/event_dates.html', form=form, show_screen_dates=show_screen_dates)


class RHDeleteEvent(RHManageEventBase):
    """Delete an event."""

    def _process_GET(self):
        return jsonify_template('events/management/delete_event.html', event=self.event_new)

    def _process_POST(self):
        delete_event(self.event_new)
        flash(_('Event "{}" successfully deleted.').format(self.event_new.title), 'success')
        category = self.event_new.category
        if category.can_manage(session.user):
            redirect_url = url_for('categories.manage_content', category)
        elif category.can_access(session.user):
            redirect_url = url_for('categories.display', category)
        else:
            redirect_url = url_for_index()
        return jsonify_data(flash=False, redirect=redirect_url)


class RHChangeEventType(RHManageEventBase):
    """Change the type of an event"""

    def _process(self):
        type_ = EventType[request.form['type']]
        update_event_type(self.event_new, type_)
        flash(_('The event type has been changed to {}.').format(type_.title), 'success')
        return jsonify_data(flash=False, redirect=url_for('.settings', self.event_new))


class RHLockEvent(RHManageEventBase):
    """Lock an event."""

    def _checkProtection(self):
        RHManageEventBase._checkProtection(self)
        if not can_lock(self.event_new, session.user):
            raise Forbidden

    def _process_GET(self):
        return jsonify_template('events/management/lock_event.html')

    def _process_POST(self):
        lock_event(self.event_new)
        flash(_('The event is now locked.'), 'success')
        return jsonify_data(flash=False, redirect=url_for('.settings', self.event_new))


class RHUnlockEvent(RHManageEventBase):
    """Unlock an event."""

    def _checkProtection(self):
        self._allowClosed = can_lock(self.event_new, session.user)
        RHManageEventBase._checkProtection(self)

    def _process(self):
        unlock_event(self.event_new)
        flash(_('The event is now unlocked.'), 'success')
        return redirect(url_for('event_management.settings', self.event_new))


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


class RHShowNonInheriting(RHManageEventBase):
    """Show a list of non-inheriting child objects"""

    def _checkParams(self, params):
        RHManageEventBase._checkParams(self, params)
        self.obj = get_object_from_args()[2]
        if self.obj is None:
            raise NotFound

    def _process(self):
        objects = self.obj.get_non_inheriting_objects()
        return jsonify_template('events/management/non_inheriting_objects.html', objects=objects)


class RHEventACL(RHManageEventBase):
    """Display the inherited ACL of the event"""

    def _process(self):
        return render_acl(self.event_new)


class RHEventACLMessage(RHManageEventBase):
    """Render the inheriting ACL message"""

    def _process(self):
        mode = ProtectionMode[request.args['mode']]
        return jsonify_template('forms/protection_field_acl_message.html', object=self.event_new, mode=mode,
                                endpoint='event_management.acl')


class RHEventProtection(RHManageEventBase):
    """Show event protection"""

    def _process(self):
        form = EventProtectionForm(obj=FormDefaults(**self._get_defaults()), event=self.event_new)
        if form.validate_on_submit():
            update_event_protection(self.event_new, {'protection_mode': form.protection_mode.data,
                                                     'own_no_access_contact': form.own_no_access_contact.data,
                                                     'access_key': form.access_key.data,
                                                     'visibility': form.visibility.data})
            update_object_principals(self.event_new, form.acl.data, read_access=True)
            update_object_principals(self.event_new, form.managers.data, full_access=True)
            update_object_principals(self.event_new, form.submitters.data, role='submit')
            self._update_session_coordinator_privs(form)
            flash(_('Protection settings have been updated'), 'success')
            return redirect(url_for('.protection', self.event_new))
        return WPEventProtection.render_template('event_protection.html', self._conf, form=form, event=self.event_new)

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
                     'access_key': self.event_new.access_key, 'visibility': self.event_new.visibility,
                     'own_no_access_contact': self.event_new.own_no_access_contact}, **coordinator_privs)

    def _update_session_coordinator_privs(self, form):
        data = {field: getattr(form, field).data for field in form.priv_fields}
        update_session_coordinator_privs(self.event_new, data)


class RHMoveEvent(RHManageEventBase):
    """Move event to a different category"""

    def _checkParams(self, params):
        RHManageEventBase._checkParams(self, params)
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


class RHPosterPrintSettings(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.template_id = request.args.get('template_id')

    def _process(self):
        self.commit = False
        form = PosterPrintingForm(self.event_new, template=self.template_id)
        if form.validate_on_submit():
            data = dict(form.data)
            template_id = data.pop('template')
            key = unicode(uuid.uuid4())
            poster_cache.set(key, data, time=1800)
            download_url = url_for('.print_poster', self.event_new, template_id=template_id, uuid=key)
            return jsonify_data(flash=False, redirect=download_url)
        return jsonify_form(form, disabled_until_change=False, submit=_('Download PDF'), )


class RHPrintEventPoster(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.template = DesignerTemplate.find_one(id=request.view_args['template_id'])

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)

        # Check that template belongs to this event or a category that
        # is a parent
        if self.template.owner != self.event_new and self.template.owner.id not in self.event_new.category_chain:
            raise Forbidden

    def _process(self):
        self.commit = False
        config_params = poster_cache.get(request.view_args['uuid'])
        if not config_params:
            raise NotFound

        pdf = PosterPDF(self.template, config_params, self.event_new)
        return send_file('Poster-{}.pdf'.format(self.event_new.id), pdf.get_pdf(), 'application/pdf')
