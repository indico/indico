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

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.agreements.base import AgreementPersonInfo, AgreementDefinitionBase, EmailPlaceholderBase
from indico.modules.events.agreements.models.agreements import Agreement
from indico.modules.events.agreements.util import get_agreement_definitions
from indico.web.flask.util import url_for
from MaKaC.webinterface.wcomponents import SideMenuItem


__all__ = ('AgreementPersonInfo', 'AgreementDefinitionBase', 'EmailPlaceholderBase')

logger = Logger.get('agreements')


@signals.app_created.connect
def _check_agreement_definitions(app, **kwargs):
    # This will raise RuntimeError if the agreement definition types are not unique
    get_agreement_definitions()


@signals.event_management.sidemenu.connect
def _extend_event_management_menu(event, **kwargs):
    return 'agreements', SideMenuItem('Agreements', url_for('agreements.event_agreements', event),
                                      visible=bool(get_agreement_definitions()) and event.canModify(session.avatar))


@signals.merge_users.connect
def _merge_users(user, merged, **kwargs):
    new_id = int(user.id)
    old_id = int(merged.id)
    Agreement.find(user_id=old_id).update({'user_id': new_id})
