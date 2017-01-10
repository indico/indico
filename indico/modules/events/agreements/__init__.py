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

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.agreements.base import AgreementPersonInfo, AgreementDefinitionBase
from indico.modules.events.agreements.models.agreements import Agreement
from indico.modules.events.agreements.placeholders import PersonNamePlaceholder, AgreementLinkPlaceholder
from indico.modules.events.agreements.util import get_agreement_definitions
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('AgreementPersonInfo', 'AgreementDefinitionBase')

logger = Logger.get('agreements')


@signals.app_created.connect
def _check_agreement_definitions(app, **kwargs):
    # This will raise RuntimeError if the agreement definition types are not unique
    get_agreement_definitions()


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not get_agreement_definitions():
        return
    if not event.can_manage(session.user):
        return
    return SideMenuItem('agreements', _('Agreements'), url_for('agreements.event_agreements', event),
                        section='services')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    Agreement.find(user_id=source.id).update({Agreement.user_id: target.id})


@signals.get_placeholders.connect_via('agreement-email')
def _get_placeholders(sender, agreement, definition, **kwargs):
    yield PersonNamePlaceholder
    yield AgreementLinkPlaceholder
