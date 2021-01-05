# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, SideMenuSection


@signals.menu.sections.connect_via('event-management-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    yield SideMenuSection('organization', _("Organization"), 60, icon='list', active=True)
    yield SideMenuSection('workflows', _("Workflows"), 55, icon="hammer")
    yield SideMenuSection('services', _("Services"), 40, icon='broadcast')
    yield SideMenuSection('reports', _("Reports"), 30, icon='stack')
    yield SideMenuSection('customization', _("Customization"), 20, icon='image')
    yield SideMenuSection('advanced', _("Advanced options"), 10, icon='lamp')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    from indico.modules.events.models.events import EventType
    if event.can_manage(session.user):
        yield SideMenuItem('settings', _('Settings'), url_for('event_management.settings', event), 100, icon='settings')
        yield SideMenuItem('protection', _('Protection'), url_for('event_management.protection', event),
                           70, icon='shield')
        if event.type_ == EventType.conference:
            yield SideMenuItem('program_codes', _('Programme Codes'), url_for('event_management.program_codes', event),
                               section='advanced')


@signals.get_placeholders.connect_via('program-codes-contribution')
def _get_placeholders(sender, contribution, **kwargs):
    from . import program_codes as pc
    yield pc.ContributionIDPlaceholder
    yield pc.ContributionSessionCodePlaceholder
    yield pc.ContributionSessionBlockCodePlaceholder
    yield pc.ContributionTrackCodePlaceholder
    yield pc.ContributionYearPlaceholder
    yield pc.ContributionMonthPlaceholder
    yield pc.ContributionDayPlaceholder
    yield pc.ContributionWeekday2Placeholder
    yield pc.ContributionWeekday3Placeholder


@signals.get_placeholders.connect_via('program-codes-subcontribution')
def _get_subcontribution_program_codes_placeholders(sender, subcontribution, **kwargs):
    from . import program_codes as pc
    yield pc.SubContributionIDPlaceholder
    yield pc.SubContributionContributionCodePlaceholder


@signals.get_placeholders.connect_via('program-codes-session')
def _get_program_codes_session_placeholders(sender, session, **kwargs):
    from . import program_codes as pc
    yield pc.SessionIDPlaceholder
    yield pc.SessionSessionTypeCodePlaceholder


@signals.get_placeholders.connect_via('program-codes-session-block')
def _get_program_codes_session_block_placeholders(sender, session_block, **kwargs):
    from . import program_codes as pc
    yield pc.SessionBlockSessionCodePlaceholder
    yield pc.SessionBlockYearPlaceholder
    yield pc.SessionBlockMonthPlaceholder
    yield pc.SessionBlockDayPlaceholder
    yield pc.SessionBlockWeekday2Placeholder
    yield pc.SessionBlockWeekday3Placeholder
