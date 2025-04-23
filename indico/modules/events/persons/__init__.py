# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.settings import EventSettingsProxy
from indico.modules.users import EnumConverter
from indico.util.enum import RichIntEnum
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.persons')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    if event.can_manage(session.user):
        return SideMenuItem('persons', _('Participant Roles'), url_for('persons.person_list', event),
                            section='organization')


@signals.core.get_placeholders.connect_via('event-persons-email')
def _get_placeholders(sender, person, event, contribution=None, abstract=None, register_link=False, object_context=None,
                      **kwargs):
    from indico.modules.events import placeholders as event_placeholders
    from indico.modules.events.persons import placeholders as person_placeholders

    yield person_placeholders.FirstNamePlaceholder
    yield person_placeholders.LastNamePlaceholder
    yield person_placeholders.EmailPlaceholder
    yield event_placeholders.EventTitlePlaceholder
    yield event_placeholders.EventLinkPlaceholder
    if register_link:
        yield person_placeholders.RegisterLinkPlaceholder
    if object_context == 'abstracts':
        yield person_placeholders.AbstractIDPlaceholder
        yield person_placeholders.AbstractTitlePlaceholder
    elif object_context == 'contributions':
        yield person_placeholders.ContributionIDPlaceholder
        yield person_placeholders.ContributionTitlePlaceholder
        yield person_placeholders.ContributionCodePlaceholder
        yield person_placeholders.ContributionDurationPlaceholder
        yield person_placeholders.ContributionSchedulePlaceholder
    else:
        yield person_placeholders.ContributionsPlaceholder


class CustomPersonsMode(RichIntEnum):
    __titles__ = [None, _('Always'), _('After search'), _('Never')]
    always = 1  # Allow submitters to add people manually
    after_search = 2  # Prevent submitters from adding people manually before searching
    never = 3  # Disallow submitters from adding people manually


persons_settings = EventSettingsProxy('persons', {
    'custom_persons_mode': CustomPersonsMode.always,
    'default_search_external': False,  # Enable "Users with no Indico account" by default
    'show_titles': True,  # Whether to show titles for people in the event
}, converters={'custom_persons_mode': EnumConverter(CustomPersonsMode)})
