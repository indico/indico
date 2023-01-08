# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

from indico.web.flask.templating import get_template_module


def _assert_snapshot(snapshot, template_name, **context):
    __tracebackhide__ = True
    template = get_template_module(f'events/editing/emails/{template_name}', **context)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), template_name)


def test_confirmation_email_plaintext(snapshot):
    _assert_snapshot(snapshot, 'submitter_confirmation_notification.txt',
                     recipient_name='John Doe',
                     submitter_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url')


def test_comment_email_plaintext(snapshot):
    _assert_snapshot(snapshot, 'comment_notification.txt',
                     recipient_name='John Doe',
                     author_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url')


def test_upload_email_plaintext(snapshot):
    _assert_snapshot(snapshot, 'submitter_upload_notification.txt',
                     recipient_name='John Doe',
                     submitter_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url')


def test_rejection_email_plaintext(snapshot):
    _assert_snapshot(snapshot, 'submitter_rejection_notification.txt',
                     recipient_name='John Doe',
                     submitter_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url')


def test_judgment_email_plaintext(snapshot):
    _assert_snapshot(snapshot, 'editor_judgment_notification.txt',
                     recipient_name='John Doe',
                     editor_name='Jane Doe',
                     timeline_url='http://localhost/timeline-url')
