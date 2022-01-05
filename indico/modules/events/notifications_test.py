# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

import pytest

from indico.web.flask.templating import get_template_module


@pytest.mark.parametrize(('num_events', 'comment', 'snapshot_name'), (
    (1, '', 'move-request-new-single-nocomment.txt'),
    (2, '', 'move-request-new-multi-nocomment.txt'),
    (1, 'Please move this.\nThanks!', 'move-request-new-single-comment.txt'),
    (2, 'Please move this.\nThanks!', 'move-request-new-multi-comment.txt'),
))
def test_move_request_creation_email_plaintext(snapshot, create_category, create_event, num_events, comment,
                                               snapshot_name):
    cat = create_category(id_=314, title='target')
    events = [create_event(id_=n, title=f'test {n}') for n in range(1, num_events + 1)]
    template = get_template_module('events/emails/move_request_creation.txt',
                                   events=events, target_category=cat, comment=comment)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), snapshot_name)


@pytest.mark.parametrize(('accept', 'num_events', 'reason', 'snapshot_name'), (
    (False, 1, '', 'move-request-rejected-single-noreason.txt'),
    (False, 2, '', 'move-request-rejected-multi-noreason.txt'),
    (False, 1, 'We do not want your event.\nSorry not sorry.', 'move-request-rejected-single-reason.txt'),
    (False, 2, 'We do not want your event.\nSorry not sorry.', 'move-request-rejected-multi-reason.txt'),
    (True, 1, '', 'move-request-accepted-single.txt'),
    (True, 2, '', 'move-request-accepted-multi.txt'),
))
def test_move_request_closed_email_plaintext(snapshot, create_category, create_event, accept, num_events, reason,
                                             snapshot_name):
    cat = create_category(id_=314, title='target')
    events = [create_event(id_=n, title=f'test {n}') for n in range(1, num_events + 1)]
    template = get_template_module('events/emails/move_request_closure.txt',
                                   events=events, target_category=cat, accept=accept, reason=reason)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), snapshot_name)
