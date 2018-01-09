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
from indico.core.roles import ManagementRole
from indico.modules.events.features.base import EventFeature
from indico.modules.events.models.events import Event, EventType
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.papers')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.cfp.is_manager(session.user) or not PapersFeature.is_allowed_for_event(event):
        return
    return SideMenuItem('papers', _('Call for Papers'), url_for('papers.management', event),
                        section='organization')


@signals.event_management.management_url.connect
def _get_event_management_url(event, **kwargs):
    if event.cfp.is_manager(session.user):
        return url_for('papers.management', event)


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return PapersFeature


@signals.acl.get_management_roles.connect_via(Event)
def _get_management_roles(sender, **kwargs):
    yield PaperManagerRole
    yield PaperJudgeRole
    yield PaperContentReviewerRole
    yield PaperLayoutReviewerRole


class PapersFeature(EventFeature):
    name = 'papers'
    friendly_name = _('Call for Papers')
    description = _('Gives event managers the opportunity to open a "Call for Papers" and use the paper '
                    'reviewing workflow.')

    @classmethod
    def is_allowed_for_event(cls, event):
        return event.type_ == EventType.conference


class PaperManagerRole(ManagementRole):
    name = 'paper_manager'
    friendly_name = _('Paper Manager')
    description = _('Grants management rights for paper reviewing on an event.')


class PaperJudgeRole(ManagementRole):
    name = 'paper_judge'
    friendly_name = _('Judge')
    description = _('Grants paper judgment rights for assigned papers.')


class PaperContentReviewerRole(ManagementRole):
    name = 'paper_content_reviewer'
    friendly_name = _('Content reviewer')
    description = _('Grants content reviewing rights for assigned papers.')


class PaperLayoutReviewerRole(ManagementRole):
    name = 'paper_layout_reviewer'
    friendly_name = _('Layout reviewer')
    description = _('Grants layout reviewing rights for assigned papers.')


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    from indico.modules.events.layout.util import MenuEntryData

    def _judging_area_visible(event):
        if not session.user or not event.has_feature('papers'):
            return False
        return event.cfp.can_access_judging_area(session.user)

    def _reviewing_area_visible(event):
        if not session.user or not event.has_feature('papers'):
            return False
        return event.cfp.can_access_reviewing_area(session.user)

    def _call_for_papers_visible(event):
        from indico.modules.events.papers.util import has_contributions_with_user_paper_submission_rights
        if not session.user or not event.has_feature('papers'):
            return False
        return (has_contributions_with_user_paper_submission_rights(event, session.user) or
                event.cfp.is_staff(session.user))

    yield MenuEntryData(title=_("Call for Papers"), name='call_for_papers',
                        endpoint='papers.call_for_papers', position=8,
                        visible=_call_for_papers_visible)

    yield MenuEntryData(title=_("Reviewing Area"), name='paper_reviewing_area', parent='call_for_papers',
                        endpoint='papers.reviewing_area', position=0, visible=_reviewing_area_visible)

    yield MenuEntryData(title=_("Judging Area"), name='paper_judging_area', parent='call_for_papers',
                        endpoint='papers.papers_list', position=1, visible=_judging_area_visible)
