# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta
from io import BytesIO

import pytest
from pytz import utc

from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.notes.models.notes import EventNote, RenderMode


pytest_plugins = 'indico.modules.events.timetable.testing.fixtures'


def test_dump_event(db, dummy_user, dummy_event):
    from indico.modules.search.schemas import EventSchema
    schema = EventSchema()
    dummy_event.description = 'A dummy event'
    dummy_event.keywords = ['foo', 'bar']
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    person2 = EventPerson(event=dummy_event, first_name='Admin', last_name='Saurus', affiliation='Indico')
    dummy_event.person_links.append(EventPersonLink(person=person))
    dummy_event.person_links.append(EventPersonLink(person=person2))
    db.session.flush()
    category_id = dummy_event.category_id
    assert schema.dump(dummy_event) == {
        'description': 'A dummy event',
        'keywords': ['foo', 'bar'],
        'location': {'address': '', 'room_name': '', 'venue_name': ''},
        'persons': [{'affiliation': None, 'name': 'Guinea Pig'},
                    {'affiliation': 'Indico', 'name': 'Admin Saurus'}],
        'title': 'dummy#0',
        'category_id': category_id,
        'category_path': [
            {'id': 0, 'title': 'Home', 'url': '/'},
            {'id': category_id, 'title': 'dummy', 'url': f'/category/{category_id}/'},
        ],
        'end_dt': dummy_event.end_dt.isoformat(),
        'event_id': 0,
        'start_dt': dummy_event.start_dt.isoformat(),
        'type': 'event',
        'event_type': 'meeting',
        'url': '/event/0/',
    }


@pytest.mark.parametrize('scheduled', (False, True))
def test_dump_contribution(db, dummy_user, dummy_event, dummy_contribution, create_entry, scheduled):
    from indico.modules.search.schemas import ContributionSchema

    person = EventPerson.create_from_user(dummy_user, dummy_event)
    dummy_contribution.person_links.append(ContributionPersonLink(person=person))
    dummy_contribution.description = 'A dummy contribution'

    extra = {'start_dt': None, 'end_dt': None}
    if scheduled:
        create_entry(dummy_contribution, utc.localize(datetime(2020, 4, 20, 4, 20)))
        extra = {
            'start_dt': dummy_contribution.start_dt.isoformat(),
            'end_dt': dummy_contribution.end_dt.isoformat(),
        }

    db.session.flush()
    category_id = dummy_contribution.event.category_id
    schema = ContributionSchema()
    assert schema.dump(dummy_contribution) == {
        'description': 'A dummy contribution',
        'location': {'address': '', 'room_name': '', 'venue_name': ''},
        'persons': [{'affiliation': None, 'name': 'Guinea Pig'}],
        'title': 'Dummy Contribution',
        'category_id': category_id,
        'category_path': [
            {'id': 0, 'title': 'Home', 'url': '/'},
            {'id': category_id, 'title': 'dummy', 'url': f'/category/{category_id}/'},
        ],
        'contribution_id': dummy_contribution.id,
        'duration': 20,
        'event_id': 0,
        'type': 'contribution',
        'url': f'/event/0/contributions/{dummy_contribution.id}/',
        **extra
    }


@pytest.mark.parametrize('scheduled', (False, True))
def test_dump_subcontribution(db, dummy_user, dummy_event, dummy_contribution, create_entry, scheduled):
    from indico.modules.search.schemas import SubContributionSchema

    extra = {'start_dt': None, 'end_dt': None}
    if scheduled:
        create_entry(dummy_contribution, utc.localize(datetime(2020, 4, 20, 4, 20)))
        extra = {
            'start_dt': dummy_contribution.start_dt.isoformat(),
            'end_dt': dummy_contribution.end_dt.isoformat(),
        }

    subcontribution = SubContribution(contribution=dummy_contribution, title='Dummy Subcontribution',
                                      description='A dummy subcontribution',
                                      duration=timedelta(minutes=10))

    person = EventPerson.create_from_user(dummy_user, dummy_event)
    subcontribution.person_links.append(SubContributionPersonLink(person=person))

    db.session.flush()
    category_id = dummy_contribution.event.category_id
    schema = SubContributionSchema()
    assert schema.dump(subcontribution) == {
        'description': 'A dummy subcontribution',
        'location': {'address': '', 'room_name': '', 'venue_name': ''},
        'persons': [{'affiliation': None, 'name': 'Guinea Pig'}],
        'title': 'Dummy Subcontribution',
        'category_id': category_id,
        'category_path': [
            {'id': 0, 'title': 'Home', 'url': '/'},
            {'id': category_id, 'title': 'dummy', 'url': f'/category/{category_id}/'},
        ],
        'contribution_id': dummy_contribution.id,
        'duration': 10,
        'event_id': 0,
        'subcontribution_id': subcontribution.id,
        'type': 'subcontribution',
        'url': f'/event/0/contributions/{dummy_contribution.id}/subcontributions/{subcontribution.id}',
        **extra
    }


def test_dump_attachment(db, dummy_user, dummy_contribution):
    from indico.modules.search.schemas import AttachmentSchema

    folder = AttachmentFolder(title='Dummy Folder', description='a dummy folder')
    file = AttachmentFile(user=dummy_user, filename='dummy_file.txt', content_type='text/plain')
    attachment = Attachment(folder=folder, user=dummy_user, title='Dummy Attachment', type=AttachmentType.file,
                            file=file)
    attachment.folder.object = dummy_contribution
    attachment.file.save(BytesIO(b'hello world'))
    db.session.flush()

    category_id = dummy_contribution.event.category_id
    schema = AttachmentSchema()
    assert schema.dump(attachment) == {
        'filename': 'dummy_file.txt',
        'title': 'Dummy Attachment',
        'user': {'affiliation': None, 'name': 'Guinea Pig'},
        'attachment_id': attachment.id,
        'attachment_type': 'file',
        'category_id': category_id,
        'category_path': [
            {'id': 0, 'title': 'Home', 'url': '/'},
            {'id': category_id, 'title': 'dummy', 'url': f'/category/{category_id}/'},
        ],
        'contribution_id': dummy_contribution.id,
        'subcontribution_id': None,
        'event_id': 0,
        'folder_id': folder.id,
        'modified_dt': attachment.modified_dt.isoformat(),
        'type': 'attachment',
        'url': (
            f'/event/0/contributions/'
            f'{dummy_contribution.id}/attachments/{folder.id}/{attachment.id}/dummy_file.txt'
        ),
    }


@pytest.mark.parametrize('link_type', ('event', 'contrib', 'subcontrib'))
def test_dump_event_note(db, dummy_user, dummy_event, dummy_contribution, link_type):
    from indico.modules.search.schemas import EventNoteSchema

    if link_type == 'event':
        ids = {'contribution_id': None, 'subcontribution_id': None}
        note = EventNote(object=dummy_event)
        url = '/event/0/note/'
    elif link_type == 'contrib':
        ids = {'contribution_id': dummy_contribution.id, 'subcontribution_id': None}
        note = EventNote(object=dummy_contribution)
        url = f'/event/0/contributions/{dummy_contribution.id}/note/'
    elif link_type == 'subcontrib':
        subcontribution = SubContribution(contribution=dummy_contribution, title='Dummy Subcontribution',
                                          duration=timedelta(minutes=10))
        db.session.flush()
        ids = {
            'contribution_id': subcontribution.contribution_id,
            'subcontribution_id': subcontribution.id,
        }
        note = EventNote(object=subcontribution)
        url = f'/event/0/contributions/{dummy_contribution.id}/subcontributions/{subcontribution.id}/note/'

    note.create_revision(RenderMode.html, 'this is a dummy note', dummy_user)
    db.session.flush()
    category_id = dummy_event.category_id
    schema = EventNoteSchema()
    assert schema.dump(note) == {
        'content': 'this is a dummy note',
        'user': {'affiliation': None, 'name': 'Guinea Pig'},
        'category_id': category_id,
        'category_path': [
            {'id': 0, 'title': 'Home', 'url': '/'},
            {'id': category_id, 'title': 'dummy', 'url': f'/category/{category_id}/'},
        ],
        'modified_dt': note.current_revision.created_dt.isoformat(),
        'event_id': 0,
        'note_id': note.id,
        'title': note.object.title,
        'type': 'event_note',
        'url': url,
        **ids
    }
