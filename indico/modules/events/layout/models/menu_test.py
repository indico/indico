# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories.models.roles import CategoryRole
from indico.modules.events.contributions.models.persons import SubContributionPersonLink
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.layout.models.menu import EventPage, MenuEntry, MenuEntryType
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.roles import EventRole


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_update_principal(
    db,
    dummy_user,
    dummy_event,
    dummy_group,
    create_user,
    dummy_contribution,
    dummy_regform,
    create_registration,
    create_category,
):
    menu_page = EventPage(event=dummy_event, html='')
    menu_entry = MenuEntry(
        id=1,
        event=dummy_event,
        type=MenuEntryType.page,
        page=menu_page,
        title='Test Page',
        protection_mode=ProtectionMode.inheriting,
    )
    assert not menu_entry.acl_entries
    # Event is public by default, menu entry inherits
    assert menu_entry.can_access(dummy_user)

    # With our event protected, the user should not have access
    dummy_event.protection_mode = ProtectionMode.protected
    assert not menu_entry.can_access(dummy_user)

    # Giving the user access to the event should regain access
    dummy_event.update_principal(dummy_user, read_access=True)
    assert menu_entry.can_access(dummy_user)

    # Now do a number of checks with a protected entry. By default the user
    # does not have access
    menu_entry.protection_mode = ProtectionMode.protected
    assert not menu_entry.can_access(dummy_user)

    # Add a user
    entry = menu_entry.update_principal(dummy_user, read_access=True)
    assert menu_entry.acl_entries == {entry}
    assert menu_entry.can_access(dummy_user)

    # Add a group with a user
    groupuser = create_user(123, groups={dummy_group})
    dummy_event.update_principal(dummy_group, read_access=True)
    assert not menu_entry.can_access(groupuser)
    entry = menu_entry.update_principal(dummy_group, read_access=True)
    assert entry in menu_entry.acl_entries
    assert menu_entry.can_access(groupuser)

    # Add a registration form principal
    set_feature_enabled(dummy_event, 'registration', True)
    reguser = create_user(234)
    person = EventPerson.create_from_user(reguser, dummy_event)
    dummy_event.registrations.append(create_registration(reguser, dummy_regform))
    dummy_event.update_principal(dummy_regform, read_access=True)
    assert not menu_entry.can_access(reguser)
    entry = menu_entry.update_principal(dummy_regform, read_access=True)
    assert entry in menu_entry.acl_entries
    assert menu_entry.can_access(reguser)

    # Add a category role
    catuser = create_user(345)
    category = create_category(25, title='target')
    category_role = CategoryRole(category=category, name='category', code='CAT', color='005272')
    db.session.flush()
    category_role.members.add(catuser)
    dummy_event.update_principal(category_role, read_access=True)
    assert not menu_entry.can_access(catuser)
    entry = menu_entry.update_principal(category_role, read_access=True)
    assert entry in menu_entry.acl_entries
    assert menu_entry.can_access(catuser)

    # Add an event role
    eventuser = create_user(567)
    event_role = EventRole(event=dummy_event, name='eventrole', code='EVT', color='005272')
    db.session.flush()
    event_role.members.add(eventuser)
    dummy_event.update_principal(eventuser, read_access=True)
    assert not menu_entry.can_access(eventuser)
    entry = menu_entry.update_principal(event_role, read_access=True)
    assert entry in menu_entry.acl_entries
    assert menu_entry.can_access(eventuser)

    # Allow Speakers
    speakeruser = create_user(678)
    person = EventPerson.create_from_user(speakeruser, dummy_event)
    assert not menu_entry.can_access(speakeruser)
    subcontrib = SubContribution(contribution=dummy_contribution, title='sc', duration=timedelta(minutes=10))
    subcontrib_person_link = SubContributionPersonLink(person=person)
    subcontrib.person_links.append(subcontrib_person_link)
    assert not menu_entry.can_access(speakeruser)
    menu_entry.speakers_can_access = True
    assert menu_entry.can_access(speakeruser)
