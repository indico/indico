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

from flask import session, render_template, flash

from indico.core import signals
from indico.core.db import db
from indico.core.logger import Logger
from indico.core.roles import ManagementRole
from indico.modules.events import Event
from indico.modules.events.features.base import EventFeature
from indico.modules.events.layout.util import MenuEntryData
from indico.util.i18n import _, ngettext
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem

logger = Logger.get('events.registration')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.has_feature('registration') or not event.can_manage(session.user, 'registration', allow_key=True):
        return
    return SideMenuItem('registration', _('Registration'), url_for('event_registration.manage_regform_list', event),
                        section='organization')


def _get_open_regforms(event):
    if not event.has_feature('registration'):
        return []
    from indico.modules.events.registration.models.forms import RegistrationForm
    return (RegistrationForm.find(RegistrationForm.is_open, event_id=int(event.id))
                            .order_by(db.func.lower(RegistrationForm.title))
                            .all())


@template_hook('conference-home-info')
def _inject_regform_announcement(event, **kwargs):
    from indico.modules.events.registration.util import user_registered_in_event, get_registrations_with_tickets
    regforms = _get_open_regforms(event)
    if regforms:
        return render_template('events/registration/display/conference_home.html', regforms=regforms, event=event,
                               user_has_registered=(session.user and user_registered_in_event(session.user, event)),
                               registrations_with_tickets=get_registrations_with_tickets(session.user, event))


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    from indico.modules.events.registration.models.forms import RegistrationForm
    from indico.modules.events.registration.models.registrations import Registration

    def _visible_registration(event):
        if not event.has_feature('registration'):
            return False
        if RegistrationForm.find(RegistrationForm.is_scheduled, RegistrationForm.event_id == int(event.id)).count():
            return True
        if not session.user:
            return False
        return bool(Registration.find(Registration.user == session.user,
                                      ~Registration.is_deleted,
                                      ~RegistrationForm.is_deleted,
                                      _join=Registration.registration_form).count())

    def _visible_participant_list(event):
        if not event.has_feature('registration'):
            return False
        return bool(RegistrationForm.find(RegistrationForm.publish_registrations_enabled,
                                          RegistrationForm.event_id == int(event.id)).count())

    yield MenuEntryData(_('Registration'), 'registration', 'event_registration.display_regform_list', position=10,
                        visible=_visible_registration)
    yield MenuEntryData(_('Participant List'), 'participants', 'event_registration.participant_list', position=11,
                        visible=_visible_participant_list)


@signals.users.registered.connect
@signals.users.email_added.connect
def _associate_registrations(user, **kwargs):
    from indico.modules.events.registration.models.registrations import Registration
    reg_alias = db.aliased(Registration)
    subquery = db.session.query(reg_alias).filter(reg_alias.user_id == user.id,
                                                  reg_alias.registration_form_id == Registration.registration_form_id,
                                                  ~reg_alias.is_deleted)
    registrations = (Registration
                     .find(Registration.user_id == None,  # noqa
                           Registration.email.in_(user.all_emails),
                           ~subquery.exists(),
                           ~Registration.is_deleted)
                     .order_by(Registration.submitted_dt.desc())
                     .all())
    if not registrations:
        return
    done = set()
    for registration in registrations:
        if registration.registration_form_id in done:
            continue
        logger.info('Associating %s with %s', registration, user)
        registration.user = user
        done.add(registration.registration_form_id)
    db.session.flush()
    num = len(done)
    flash(ngettext("A registration has been linked to your account.",
                   "{n} registrations have been linked to your account.", num).format(n=num), 'info')


@signals.event_management.management_url.connect
def _get_event_management_url(event, **kwargs):
    if event.as_event.can_manage(session.user, role='registration'):
        return url_for('event_registration.manage_regform_list', event)


@signals.get_placeholders.connect_via('registration-invitation-email')
def _get_invitation_placeholders(sender, invitation, **kwargs):
    from indico.modules.events.registration.placeholders.invitations import (FirstNamePlaceholder, LastNamePlaceholder,
                                                                             InvitationLinkPlaceholder)

    yield FirstNamePlaceholder
    yield LastNamePlaceholder
    yield InvitationLinkPlaceholder


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return RegistrationFeature


@signals.acl.get_management_roles.connect_via(Event)
def _get_management_roles(sender, **kwargs):
    return RegistrationRole


@signals.get_placeholders.connect_via('registration-email')
def _get_registration_placeholders(sender, registration, **kwargs):
    from indico.modules.events.registration.placeholders.registrations import (IDPlaceholder, LastNamePlaceholder,
                                                                               FirstNamePlaceholder, LinkPlaceholder,
                                                                               EventTitlePlaceholder,
                                                                               EventLinkPlaceholder)

    yield FirstNamePlaceholder
    yield LastNamePlaceholder
    yield EventTitlePlaceholder
    yield EventLinkPlaceholder
    yield IDPlaceholder
    yield LinkPlaceholder


class RegistrationFeature(EventFeature):
    name = 'registration'
    friendly_name = _('Registration')
    description = _('Gives event managers the opportunity to handle registrations within the event.')

    @classmethod
    def is_default_for_event(cls, event):
        return event.getType() == 'conference'


class RegistrationRole(ManagementRole):
    name = 'registration'
    friendly_name = _('Registration')
    description = _('Grants management access to the registration form.')


@template_hook('event-header')
def _inject_event_header(event, **kwargs):
    from indico.modules.events.registration.models.forms import RegistrationForm

    event = event.as_event
    regforms = (event.registration_forms
                .filter_by(is_deleted=False, is_open=True)
                .order_by(db.func.lower(RegistrationForm.title))
                .all())

    if regforms:
        return render_template('events/registration/display/event_header.html', event=event, regforms=regforms)
