# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime
from pathlib import Path

import pytest
from itsdangerous import URLSafeSerializer

from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.notes.models.notes import EventNote
from indico.modules.events.static.models.static import StaticSite
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.export import DataExportOptions, DataExportRequest, DataExportRequestState
from indico.modules.users.models.users import NameFormat
from indico.testing.util import assert_yaml_snapshot


pytest_plugins = ('indico.modules.events.registration.testing.fixtures',
                  'indico.modules.users.testing.fixtures')

SNAPSHOT_DIR = Path(__file__).parent / 'tests'


def _assert_yaml_snapshot(snapshot, data, name):
    __tracebackhide__ = True
    snapshot.snapshot_dir = SNAPSHOT_DIR
    assert_yaml_snapshot(snapshot, data, name, strip_dynamic_data=True)


@pytest.fixture(autouse=True)
def freeze_time_for_snapshots(freeze_time):
    """Ensure the tests use the same time as the saved snapshots."""
    freeze_time(datetime(2022, 5, 22, 12, 0, 0))


@pytest.fixture(autouse=True)
def static_signature(mocker):
    """Ensure signed URLs do not change between test runs."""
    mocker.patch.object(URLSafeSerializer, 'dumps').return_value = 'signature'


def test_data_export_request_schema(db, dummy_user):
    from indico.modules.users.export_schemas import DataExportRequestSchema

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
    from indico.modules.users.export_schemas import SettingsExportSchema

    setup_settings(dummy_user.settings)
    data = SettingsExportSchema().dump(dummy_user.settings.get_all())
    _assert_yaml_snapshot(snapshot, data, 'settings_export_schema.yml')


def setup_personal_data(dummy_user, dummy_event, dummy_category):
    dummy_user.affiliation_link = Affiliation(name='CERN')
    dummy_user.affiliation = dummy_user.affiliation_link.name
    dummy_user.favorite_events.add(dummy_event)
    dummy_user.favorite_categories.add(dummy_category)


def test_personal_data_export_schema(snapshot, db, dummy_event, dummy_category, dummy_user):
    from indico.modules.users.export_schemas import PersonalDataExportSchema

    setup_personal_data(dummy_user, dummy_event, dummy_category)
    db.session.flush()

    data = PersonalDataExportSchema().dump(dummy_user)
    _assert_yaml_snapshot(snapshot, data, 'personal_data_export_schema.yml')


def setup_contributions(db, user, contribution, event_person):
    link = ContributionPersonLink(is_speaker=True, person=event_person)
    contribution.person_links = [link]

    note = EventNote(object=contribution)
    note.create_revision(RenderMode.markdown, '**Contrib Test**', user)
    db.session.add(note)


def test_contribution_export_schema(snapshot, db, dummy_user, dummy_contribution, dummy_event_person):
    from indico.modules.users.export_schemas import ContributionExportSchema

    setup_contributions(db, dummy_user, dummy_contribution, dummy_event_person)
    db.session.flush()

    data = ContributionExportSchema(context={'user': dummy_user}).dump(dummy_contribution)
    _assert_yaml_snapshot(snapshot, data, 'contribution_export_schema.yml')


def setup_subcontributions(db, user, subcontribution, event_person):
    link = SubContributionPersonLink(is_speaker=True, person=event_person)
    subcontribution.person_links = [link]

    note = EventNote(object=subcontribution)
    note.create_revision(RenderMode.markdown, '**SubContrib Test**', user)
    db.session.add(note)


def test_subcontribution_export_schema(snapshot, db, dummy_user, dummy_subcontribution, dummy_event_person):
    from indico.modules.users.export_schemas import SubContributionExportSchema

    setup_subcontributions(db, dummy_user, dummy_subcontribution, dummy_event_person)
    db.session.flush()

    data = SubContributionExportSchema(context={'user': dummy_user}).dump(dummy_subcontribution)
    _assert_yaml_snapshot(snapshot, data, 'subcontribution_export_schema.yml')


def test_registration_export_schema(snapshot, create_receipt_file, dummy_reg_with_file_field, dummy_event_template):
    from indico.modules.users.export_schemas import RegistrationExportSchema
    create_receipt_file(dummy_reg_with_file_field, dummy_event_template, id=0)

    data = RegistrationExportSchema().dump(dummy_reg_with_file_field)
    _assert_yaml_snapshot(snapshot, data, 'registration_export_schema.yml')


def setup_room_booking(user, room):
    user.favorite_rooms.add(room)
    user.owned_rooms.append(room)


@pytest.mark.usefixtures('dummy_reservation')
def test_room_booking_export_schema(snapshot, db, dummy_user, dummy_room):
    from indico.modules.users.export_schemas import RoomBookingExportSchema

    setup_room_booking(dummy_user, dummy_room)
    db.session.flush()

    data = RoomBookingExportSchema().dump(dummy_user)
    _assert_yaml_snapshot(snapshot, data, 'room_booking_export_schema.yml')


@pytest.mark.usefixtures('dummy_abstract_file')
def test_abstract_export_schema(snapshot, dummy_abstract):
    from indico.modules.users.export_schemas import AbstractExportSchema

    data = AbstractExportSchema().dump(dummy_abstract)
    _assert_yaml_snapshot(snapshot, data, 'abstract_export_schema.yml')


@pytest.mark.usefixtures('dummy_paper_file')
def test_paper_export_schema(snapshot, dummy_paper):
    from indico.modules.users.export_schemas import PaperExportSchema

    data = PaperExportSchema().dump(dummy_paper)
    _assert_yaml_snapshot(snapshot, data, 'paper_export_schema.yml')


def test_attachment_export_schema(snapshot, dummy_attachment):
    from indico.modules.users.export_schemas import AttachmentExportSchema

    data = AttachmentExportSchema().dump(dummy_attachment)
    _assert_yaml_snapshot(snapshot, data, 'attachment_export_schema.yml')


@pytest.mark.usefixtures('dummy_editing_revision_file')
def test_editable_export_schema(snapshot, dummy_editable):
    from indico.modules.users.export_schemas import EditableExportSchema

    data = EditableExportSchema().dump(dummy_editable)
    _assert_yaml_snapshot(snapshot, data, 'editable_export_schema.yml')


def setup_misc_data(user, event):
    event.creator = user
    StaticSite(creator=user, event=event)


@pytest.mark.usefixtures('dummy_app_link', 'dummy_personal_token', 'dummy_identity')
def test_misc_data_export_schema(snapshot, db, dummy_user, dummy_event):
    from indico.modules.users.export_schemas import MiscDataExportSchema

    setup_misc_data(dummy_user, dummy_event)
    db.session.flush()

    data = MiscDataExportSchema().dump(dummy_user)
    _assert_yaml_snapshot(snapshot, data, 'misc_data_export_schema.yml')


def test_empty_user_data_export_schema(snapshot, dummy_user):
    from indico.modules.users.export_schemas import UserDataExportSchema

    data = UserDataExportSchema().dump(dummy_user)
    _assert_yaml_snapshot(snapshot, data, 'empty_user_data_export_schema.yml')


@pytest.mark.parametrize('include_files', (False, True), ids=('without_files', 'with_files'))
@pytest.mark.usefixtures('dummy_reservation', 'dummy_attachment', 'dummy_abstract_file', 'dummy_paper_file',
                         'dummy_reg_with_file_field', 'dummy_editing_revision_file')
def test_user_data_export_schema(request, snapshot, db, dummy_user, dummy_category, dummy_event, dummy_contribution,
                                 dummy_subcontribution, dummy_event_person, dummy_room, include_files,
                                 create_receipt_file, dummy_reg_with_file_field, dummy_event_template):
    from indico.modules.users.export_schemas import UserDataExportSchema

    create_receipt_file(dummy_reg_with_file_field, dummy_event_template, id=0)

    setup_settings(dummy_user.settings)
    setup_personal_data(dummy_user, dummy_event, dummy_category)
    setup_contributions(db, dummy_user, dummy_contribution, dummy_event_person)
    setup_subcontributions(db, dummy_user, dummy_subcontribution, dummy_event_person)
    setup_room_booking(dummy_user, dummy_room)
    setup_misc_data(dummy_user, dummy_event)
    db.session.flush()

    data = UserDataExportSchema(context={'include_files': include_files}).dump(dummy_user)
    test_id = request.node.callspec.id
    _assert_yaml_snapshot(snapshot, data, f'user_data_export_schema_{test_id}.yml')
