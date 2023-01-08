# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import pytest

from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryAccess, MenuEntryType
from indico.modules.events.models.persons import EventPerson


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_access_everyone(dummy_contribution, dummy_user, dummy_event):
    menu_entry = MenuEntry(event=dummy_event, type=MenuEntryType.page, access=MenuEntryAccess.everyone)
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    assert menu_entry.can_access(dummy_user)
    contrib_person_link = ContributionPersonLink(person=person)
    dummy_contribution.person_links.append(contrib_person_link)
    assert menu_entry.can_access(dummy_user)
    contrib_person_link.is_speaker = True
    assert menu_entry.can_access(dummy_user)


def test_access_participants_not_registered(dummy_contribution, dummy_user, dummy_event):
    menu_entry = MenuEntry(event=dummy_event, type=MenuEntryType.page, access=MenuEntryAccess.registered_participants)
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    assert not menu_entry.can_access(dummy_user)
    contrib_person_link = ContributionPersonLink(person=person)
    dummy_contribution.person_links.append(contrib_person_link)
    assert not menu_entry.can_access(dummy_user)
    contrib_person_link.is_speaker = True
    assert not menu_entry.can_access(dummy_user)


@pytest.mark.usefixtures('dummy_reg')
def test_access_participants_registered(dummy_contribution, dummy_user, dummy_event):
    set_feature_enabled(dummy_event, 'registration', True)
    menu_entry = MenuEntry(event=dummy_event, type=MenuEntryType.page, access=MenuEntryAccess.registered_participants)
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    assert menu_entry.can_access(dummy_user)
    contrib_person_link = ContributionPersonLink(person=person)
    dummy_contribution.person_links.append(contrib_person_link)
    assert menu_entry.can_access(dummy_user)
    contrib_person_link.is_speaker = True
    assert menu_entry.can_access(dummy_user)


@pytest.mark.usefixtures('dummy_reg')
def test_access_speakers_contrib(dummy_contribution, dummy_user, dummy_event):
    set_feature_enabled(dummy_event, 'registration', True)
    menu_entry = MenuEntry(event=dummy_event, type=MenuEntryType.page, access=MenuEntryAccess.speakers)
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    assert not menu_entry.can_access(dummy_user)
    contrib_person_link = ContributionPersonLink(person=person)
    dummy_contribution.person_links.append(contrib_person_link)
    assert not menu_entry.can_access(dummy_user)
    contrib_person_link.is_speaker = True
    assert menu_entry.can_access(dummy_user)
    dummy_contribution.is_deleted = True
    assert not menu_entry.can_access(dummy_user)


@pytest.mark.usefixtures('dummy_reg')
def test_access_speakers_subcontrib(dummy_contribution, dummy_user, dummy_event):
    set_feature_enabled(dummy_event, 'registration', True)
    menu_entry = MenuEntry(event=dummy_event, type=MenuEntryType.page, access=MenuEntryAccess.speakers)
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    assert not menu_entry.can_access(dummy_user)
    subcontrib = SubContribution(contribution=dummy_contribution, title='sc', duration=timedelta(minutes=10))
    subcontrib_person_link = SubContributionPersonLink(person=person)
    subcontrib.person_links.append(subcontrib_person_link)
    assert menu_entry.can_access(dummy_user)
    dummy_contribution.is_deleted = True
    assert not menu_entry.can_access(dummy_user)
    dummy_contribution.is_deleted = False
    subcontrib.is_deleted = True
    assert not menu_entry.can_access(dummy_user)
