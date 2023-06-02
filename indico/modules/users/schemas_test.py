# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from datetime import datetime
from pathlib import Path

import freezegun
import pytest
from marshmallow import ValidationError

from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.notes.models.notes import EventNote
from indico.modules.events.static.models.static import StaticSite
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.export import DataExportOptions, DataExportRequest, DataExportRequestState
from indico.modules.users.models.users import NameFormat


pytest_plugins = ('indico.modules.events.registration.testing.fixtures',
                  'indico.modules.users.testing.fixtures')


@pytest.fixture(scope='function')
def freeze_time():
    dt = datetime(2022, 5, 22, 12, 0, 0)
    with freezegun.freeze_time(dt):
        yield


@pytest.fixture(scope='function')
def snapshot(snapshot):
    def assert_json_match(data, filename):
        __tracebackhide__ = True
        snapshot.assert_match(json.dumps(data, indent=2, sort_keys=True), filename)

    snapshot.snapshot_dir = Path(__file__).parent / 'tests'
    snapshot.assert_json_match = assert_json_match
    yield snapshot


def test_personal_data_schema():
    from indico.modules.users.schemas import UserPersonalDataSchema
    schema = UserPersonalDataSchema(partial=True)
    assert schema.load({'first_name': 'Test'}) == {'first_name': 'Test'}
    # make sure the schema rejects user columns that should never be settable
    with pytest.raises(ValidationError):
        schema.load({'first_name': 'Test', 'is_admin': True})


@pytest.mark.usefixtures('freeze_time')
def test_data_export_request_schema(db, dummy_user):
    from indico.modules.users.schemas import DataExportRequestSchema

    request = DataExportRequest(user=dummy_user, state=DataExportRequestState.running,
                                selected_options=[DataExportOptions.attachments])
    db.session.flush()

    data = DataExportRequestSchema().dump(request)
    assert data == {
        'state': 'running',
        'requested_dt': '2022-05-22T12:00:00+00:00',
        'selected_options': ['attachments'],
        'max_size_exceeded': False,
        'url': None
    }


def setup_settings(settings):
    settings.set_multi({
        'name_format': NameFormat.first_last_upper,
        'timezone': 'Europe/Paris',
        'lang': 'en_US',
        'use_previewer_pdf': False
    })


def test_settings_export_schema(snapshot, dummy_user):
    from indico.modules.users.schemas import SettingsExportSchema

    setup_settings(dummy_user.settings)
    data = SettingsExportSchema().dump(dummy_user.settings.get_all())
    snapshot.assert_json_match(data, 'settings_export_schema.json')


def setup_personal_data(dummy_user, dummy_event, dummy_category):
    dummy_user.affiliation_link = Affiliation(name='CERN')
    dummy_user.favorite_events.add(dummy_event)
    dummy_user.favorite_categories.add(dummy_category)


def test_personal_data_export_schema(snapshot, db, dummy_event, dummy_category, dummy_user):
    from indico.modules.users.schemas import PersonalDataExportSchema

    setup_personal_data(dummy_user, dummy_event, dummy_category)
    db.session.flush()

    data = PersonalDataExportSchema().dump(dummy_user)
    snapshot.assert_json_match(data, 'personal_data_export_schema.json')


def setup_contributions(db, user, contribution, event_person):
    link = ContributionPersonLink(is_speaker=True, person=event_person)
    contribution.person_links = [link]

    note = EventNote(object=contribution)
    note.create_revision(RenderMode.markdown, '**Contrib Test**', user)
    db.session.add(note)


def test_contribution_export_schema(snapshot, db, dummy_user, dummy_contribution, dummy_event_person):
    from indico.modules.users.schemas import ContributionExportSchema

    setup_contributions(db, dummy_user, dummy_contribution, dummy_event_person)
    db.session.flush()

    data = ContributionExportSchema(context={'user': dummy_user}).dump(dummy_contribution)
    snapshot.assert_json_match(data, 'contribution_export_schema.json')


def setup_subcontributions(db, user, subcontribution, event_person):
    link = SubContributionPersonLink(is_speaker=True, person=event_person)
    subcontribution.person_links = [link]

    note = EventNote(object=subcontribution)
    note.create_revision(RenderMode.markdown, '**SubContrib Test**', user)
    db.session.add(note)


def test_subcontribution_export_schema(snapshot, db, dummy_user, dummy_subcontribution, dummy_event_person):
    from indico.modules.users.schemas import SubContributionExportSchema

    setup_subcontributions(db, dummy_user, dummy_subcontribution, dummy_event_person)
    db.session.flush()

    data = SubContributionExportSchema(context={'user': dummy_user}).dump(dummy_subcontribution)
    snapshot.assert_json_match(data, 'subcontribution_export_schema.json')


@pytest.mark.usefixtures('freeze_time')
def test_registration_export_schema(snapshot, dummy_reg_with_file_field):
    """Test RegistrationExportSchema

    """
    from indico.modules.users.schemas import RegistrationExportSchema

    data = RegistrationExportSchema().dump(dummy_reg_with_file_field)
    snapshot.assert_json_match(data, 'registration_export_schema.json')


def setup_room_booking(user, room):
    user.favorite_rooms.add(room)
    user.owned_rooms.append(room)


@pytest.mark.usefixtures('freeze_time', 'dummy_reservation')
def test_room_booking_export_schema(snapshot, db, dummy_user, dummy_room):
    from indico.modules.users.schemas import RoomBookingExportSchema

    setup_room_booking(dummy_user, dummy_room)
    db.session.flush()

    data = RoomBookingExportSchema().dump(dummy_user)
    snapshot.assert_json_match(data, 'room_booking_export_schema.json')


@pytest.mark.usefixtures('freeze_time', 'dummy_abstract_file')
def test_abstract_export_schema(snapshot, dummy_abstract):
    from indico.modules.users.schemas import AbstractExportSchema

    data = AbstractExportSchema().dump(dummy_abstract)
    snapshot.assert_json_match(data, 'abstract_export_schema.json')


@pytest.mark.usefixtures('freeze_time', 'dummy_paper_file')
def test_paper_export_schema(snapshot, dummy_paper):
    from indico.modules.users.schemas import PaperExportSchema

    data = PaperExportSchema().dump(dummy_paper)
    snapshot.assert_json_match(data, 'paper_export_schema.json')


@pytest.mark.usefixtures('freeze_time')
def test_attachment_export_schema(snapshot, dummy_attachment):
    from indico.modules.users.schemas import AttachmentExportSchema

    data = AttachmentExportSchema().dump(dummy_attachment)
    snapshot.assert_json_match(data, 'attachment_export_schema.json')


@pytest.mark.usefixtures('freeze_time', 'dummy_editing_revision_file')
def test_editable_export_schema(snapshot, dummy_paper):
    from indico.modules.users.schemas import EditableExportSchema

    data = EditableExportSchema().dump(dummy_paper)
    snapshot.assert_json_match(data, 'editable_export_schema.json')


def setup_misc_data(user, event):
    event.creator = user
    StaticSite(creator=user, event=event)


@pytest.mark.usefixtures('freeze_time', 'dummy_app_link', 'dummy_personal_token', 'dummy_identity')
def test_misc_data_export_schema(snapshot, db, dummy_user, dummy_event):
    from indico.modules.users.schemas import MiscDataExportSchema

    setup_misc_data(dummy_user, dummy_event)
    db.session.flush()

    data = MiscDataExportSchema().dump(dummy_user)
    snapshot.assert_json_match(data, 'misc_data_export_schema.json')


def test_empty_user_data_export_schema(snapshot, dummy_user):
    from indico.modules.users.schemas import UserDataExportSchema

    data = UserDataExportSchema().dump(dummy_user)
    snapshot.assert_json_match(data, 'empty_user_data_export_schema.json')


@pytest.mark.usefixtures('freeze_time', 'dummy_reservation', 'dummy_attachment',
                         'dummy_abstract_file', 'dummy_paper_file',
                         'dummy_reg_with_file_field', 'dummy_editing_revision_file')
def test_user_data_export_schema(snapshot, db, dummy_user, dummy_category, dummy_event, dummy_contribution,
                                 dummy_subcontribution, dummy_event_person, dummy_room):
    from indico.modules.users.schemas import UserDataExportSchema

    setup_settings(dummy_user.settings)
    setup_personal_data(dummy_user, dummy_event, dummy_category)
    setup_contributions(db, dummy_user, dummy_contribution, dummy_event_person)
    setup_subcontributions(db, dummy_user, dummy_subcontribution, dummy_event_person)
    setup_room_booking(dummy_user, dummy_room)
    setup_misc_data(dummy_user, dummy_event)
    db.session.flush()

    data = UserDataExportSchema().dump(dummy_user)
    snapshot.assert_json_match(data, 'user_data_export_schema.json')
