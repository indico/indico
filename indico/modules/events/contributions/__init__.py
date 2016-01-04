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

from flask import flash, session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.roles import ManagementRole, check_roles
from indico.modules.events.contributions.models.contributions import Contribution
from indico.util.i18n import _, ngettext
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.contributions')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user, allow_key=True):
        return
    return SideMenuItem('contributions', _('Contributions'), url_for('contributions.manage_contributions', event),
                        section='organization')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.contributions.models.principals import ContributionPrincipal
    ContributionPrincipal.merge_users(target, source, 'contribution')


@signals.users.registered.connect
@signals.users.email_added.connect
def _convert_email_principals(user, **kwargs):
    from indico.modules.events.contributions.models.principals import ContributionPrincipal
    contributions = ContributionPrincipal.replace_email_with_user(user, 'contribution')
    if contributions:
        num = len(contributions)
        flash(ngettext("You have been granted manager/submission privileges for a contribution.",
                       "You have been granted manager/submission privileges for {} contributions.", num).format(num),
              'info')


@signals.app_created.connect
def _check_roles(app, **kwargs):
    check_roles(Contribution)


@signals.acl.get_management_roles.connect_via(Contribution)
def _get_management_roles(sender, **kwargs):
    return SubmitterRole


class SubmitterRole(ManagementRole):
    name = 'submit'
    friendly_name = _('Submission')
    description = _('Grants access to materials and minutes.')
