# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.persons')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    if event.can_manage(session.user):
        return SideMenuItem('persons', _('Roles'), url_for('persons.person_list', event), section='organization')


@signals.get_placeholders.connect_via('event-persons-email')
def _get_placeholders(sender, person, event, register_link=False, **kwargs):
    from indico.modules.events.persons.placeholders import (FirstNamePlaceholder, LastNamePlaceholder, EmailPlaceholder,
                                                            EventTitlePlaceholder, EventLinkPlaceholder,
                                                            RegisterLinkPlaceholder)
    yield FirstNamePlaceholder
    yield LastNamePlaceholder
    yield EmailPlaceholder
    yield EventTitlePlaceholder
    yield EventLinkPlaceholder
    if register_link:
        yield RegisterLinkPlaceholder
