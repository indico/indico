# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from pathlib import Path

import pytest

from indico.testing.util import assert_email_snapshot
from indico.web.flask.templating import get_template_module


def _assert_snapshot(snapshot, template_name, has_comment=False, **context):
    __tracebackhide__ = True
    template = get_template_module(f'events/editing/emails/{template_name}', **context)
    name, ext = os.path.splitext(template_name)
    comment_suffix = '_comment' if has_comment else ''
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    assert_email_snapshot(snapshot, template, f'{name}{comment_suffix}{ext}')


@pytest.mark.parametrize('has_comment', (False, True))
def test_confirmation_email_plaintext(snapshot, dummy_contribution, has_comment):
    _assert_snapshot(snapshot, 'submitter_confirmation_notification.txt', has_comment,
                     recipient_name='John Doe',
                     submitter_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url',
                     contribution=dummy_contribution,
                     text=('Great last changes' if has_comment else ''))


def test_comment_email_plaintext(snapshot, dummy_contribution):
    _assert_snapshot(snapshot, 'comment_notification.txt',
                     recipient_name='John Doe',
                     author_name='Jane Doe',
                     contribution=dummy_contribution,
                     text='The review is passed',
                     timeline_url='http://localhost/timeline-url')


def test_upload_email_plaintext(snapshot, dummy_contribution):
    _assert_snapshot(snapshot, 'submitter_upload_notification.txt',
                     recipient_name='John Doe',
                     submitter_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url',
                     contribution=dummy_contribution)


@pytest.mark.parametrize('has_comment', (False, True))
def test_rejection_email_plaintext(snapshot, dummy_contribution, has_comment):
    _assert_snapshot(snapshot, 'submitter_rejection_notification.txt', has_comment,
                     recipient_name='John Doe',
                     submitter_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url',
                     contribution=dummy_contribution,
                     text=('Revert last changes' if has_comment else ''))


@pytest.mark.parametrize('has_comment', (False, True))
def test_judgment_email_plaintext(snapshot, dummy_contribution, has_comment):
    _assert_snapshot(snapshot, 'editor_judgment_notification.txt', has_comment,
                     recipient_name='John Doe',
                     editor_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url',
                     contribution=dummy_contribution,
                     action='update',
                     text=('Added 2 slides to the presentation' if has_comment else ''))
