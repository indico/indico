# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime
from pathlib import Path

import pytest

from indico.web.flask.templating import get_template_module


@pytest.mark.parametrize(('snapshot_name'), (
    'accepted_to_event_managers.txt',
    'accepted_to_request_managers.txt',
))
def test_accepted_emails_plaintext(snapshot, snapshot_name, dummy_event):
    request = {'definition': {'title': 'More cats'}, 'comment': 'Meow',
               'created_by_user': {'full_name': 'Arthas Menethil', 'phone': '1337',
                                   'email': 'arthas@frozenthrone.wow'},
               'event_id': dummy_event.id, 'type': dummy_event.type}
    dummy_event.start_dt = datetime(2022, 11, 11, 13, 37)
    dummy_event.end_dt = datetime(2022, 11, 13, 13, 37)
    template = get_template_module(f'events/requests/emails/{snapshot_name}',
                                   req=request, event=dummy_event)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), snapshot_name)


@pytest.mark.parametrize(('snapshot_name'), (
    'new_modified_to_event_managers.txt',
    'new_modified_to_request_managers.txt',
))
def test_new_modified_emails_plaintext(snapshot, snapshot_name, dummy_event):
    request = {'definition': {'title': 'More cats'}, 'comment': 'Meow',
               'created_by_user': {'full_name': 'Arthas Menethil', 'phone': '1337',
                                   'email': 'arthas@frozenthrone.wow'},
               'event_id': dummy_event.id, 'type': dummy_event.type}
    dummy_event.start_dt = datetime(2022, 11, 11, 13, 37)
    dummy_event.end_dt = datetime(2022, 11, 13, 13, 37)
    template = get_template_module(f'events/requests/emails/{snapshot_name}',
                                   req=request, event=dummy_event, new=False)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), snapshot_name)


@pytest.mark.parametrize(('snapshot_name'), (
    'rejected_to_event_managers.txt',
    'rejected_to_request_managers.txt',
))
def test_rejected_emails_plaintext(snapshot, snapshot_name, dummy_event):
    request = {'definition': {'title': 'More cats'}, 'comment': 'Meow',
               'created_by_user': {'full_name': 'Arthas Menethil', 'phone': '1337',
                                   'email': 'arthas@frozenthrone.wow'},
               'event_id': dummy_event.id, 'type': dummy_event.type}
    dummy_event.start_dt = datetime(2022, 11, 11, 13, 37)
    dummy_event.end_dt = datetime(2022, 11, 13, 13, 37)
    template = get_template_module(f'events/requests/emails/{snapshot_name}',
                                   req=request, event=dummy_event)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), snapshot_name)


@pytest.mark.parametrize(('snapshot_name'), (
    'withdrawn_to_event_managers.txt',
    'withdrawn_to_request_managers.txt',
))
def test_withdrawn_emails_plaintext(snapshot, snapshot_name, dummy_event):
    request = {'definition': {'title': 'More cats'}, 'comment': 'Meow',
               'created_by_user': {'full_name': 'Arthas Menethil', 'phone': '1337',
                                   'email': 'arthas@frozenthrone.wow'},
               'event_id': dummy_event.id, 'type': dummy_event.type}
    dummy_event.start_dt = datetime(2022, 11, 11, 13, 37)
    dummy_event.end_dt = datetime(2022, 11, 13, 13, 37)
    template = get_template_module(f'events/requests/emails/{snapshot_name}',
                                   req=request, event=dummy_event)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), snapshot_name)
