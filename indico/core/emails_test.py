# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.core.emails import _get_actual_sender_address
from indico.modules.core.settings import core_settings


class MockConfig:
    SMTP_ALLOWED_SENDERS = {'*@example.com', 'foo@specific.com'}
    SMTP_SENDER_FALLBACK = 'sender@example.com'
    NO_REPLY_EMAIL = 'noreply@example.com'


class SMTPSenderNotSetMockConfig:
    SMTP_ALLOWED_SENDERS = {}
    SMTP_SENDER_FALLBACK = ''
    NO_REPLY_EMAIL = 'noreply@example.com'


@pytest.mark.usefixtures('db')
@pytest.mark.parametrize(('sender_email', 'sender'), (
    ('foo@example.com', 'foo@example.com'),
    ('bar@example.com', 'bar@example.com'),
    ('test@specific.com', 'Indico <sender@example.com>'),
    ('foo@specific.com', 'foo@specific.com'),
    ('Foo <foo@example.com>', 'Foo <foo@example.com>'),
    ('Bar <bar@example.com>', 'Bar <bar@example.com>'),
    ('Test <test@specific.com>', 'Test (Indico) <sender@example.com>'),
    ('Foo <foo@specific.com>', 'Foo <foo@specific.com>'),
    ('', 'Indico <noreply@example.com>'),
))
def test_get_actual_sender_address(mocker, sender_email, sender):
    mocker.patch('indico.core.emails.config', MockConfig())
    core_settings.set('site_title', 'Indico')
    actual_sender = _get_actual_sender_address(sender_email)
    assert actual_sender == sender


@pytest.mark.usefixtures('db')
@pytest.mark.parametrize(('sender_email', 'sender'), (
    ('foo@example.com', 'Indico <noreply@example.com>'),
    ('Foo <foo@example.com>', 'Foo (Indico) <noreply@example.com>'),
    ('Test <test@specific.com>', 'Test (Indico) <noreply@example.com>'),
    ('', 'Indico <noreply@example.com>'),
))
def test_smtp_sender_config_notset(mocker, sender_email, sender):
    mocker.patch('indico.core.emails.config', SMTPSenderNotSetMockConfig())
    core_settings.set('site_title', 'Indico')
    actual_sender = _get_actual_sender_address(sender_email)
    assert actual_sender == sender
