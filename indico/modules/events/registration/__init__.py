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

from flask import session, render_template

from indico.core import signals
from indico.core.db import db
from indico.core.logger import Logger
from indico.core.roles import ManagementRole
from indico.modules.events import Event
from indico.modules.events.features.base import EventFeature
from indico.util.i18n import _
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


def _get_active_regforms(event):
    if not event.has_feature('registration'):
        return []
    from indico.modules.events.registration.models.registration_forms import RegistrationForm
    return (RegistrationForm.find(RegistrationForm.is_active, RegistrationForm.event_id == int(event.id))
                            .order_by(db.func.lower(RegistrationForm.title))
                            .all())


@template_hook('conference-home-info')
def _inject_regform_announcement(event, **kwargs):
    regforms = _get_active_regforms(event)
    if regforms:
        return render_template('events/registration/display/conference_home.html', regforms=regforms, event=event)


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return RegistrationFeature


@signals.acl.get_management_roles.connect_via(Event)
def _get_management_roles(sender, **kwargs):
    return RegistrationRole


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
