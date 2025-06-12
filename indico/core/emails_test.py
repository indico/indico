# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.core.emails import get_actual_sender_address
from indico.modules.core.settings import core_settings


class MockConfig:
    SMTP_ALLOWED_SENDERS = {'*@example.com', 'foo@specific.com'}
    SMTP_SENDER_FALLBACK = 'sender@example.com'
    NO_REPLY_EMAIL = 'noreply@example.com'


class SMTPSenderNotSetMockConfig:
    SMTP_ALLOWED_SENDERS = set()
    SMTP_SENDER_FALLBACK = None
    NO_REPLY_EMAIL = 'noreply@example.com'


@pytest.mark.usefixtures('db')
@pytest.mark.parametrize(('sender_email', 'result'), (
    ('foo@example.com', ('foo@example.com', set())),
    ('bar@example.com', ('bar@example.com', set())),
    ('test@specific.com', ('"test@specific.com (via Indico)" <sender@example.com>', {'test@specific.com'})),
    ('foo@specific.com', ('foo@specific.com', set())),
    ('Foo <foo@example.com>', ('Foo <foo@example.com>', set())),
    ('Bar <bar@example.com>', ('Bar <bar@example.com>', set())),
    ('Test <test@specific.com>', ('"Test (via Indico)" <sender@example.com>', {'test@specific.com'})),
    ('Foo <foo@specific.com>', ('Foo <foo@specific.com>', set())),
    ('', ('Indico <noreply@example.com>', set())),
))
def test_get_actual_sender_address(mocker, sender_email, result):
    mocker.patch('indico.core.emails.config', MockConfig())
    core_settings.set('site_title', 'Indico')
    assert get_actual_sender_address(sender_email, set()) == result
    assert get_actual_sender_address(sender_email, {'reply@whatever.com'}) == (result[0], {'reply@whatever.com'})


@pytest.mark.usefixtures('db')
def test_get_actual_sender_address_weird_site_name(mocker):
    mocker.patch('indico.core.emails.config', MockConfig())
    core_settings.set('site_title', 'Indico @ Test')
    assert get_actual_sender_address('', set())[0] == '"Indico @ Test" <noreply@example.com>'


@pytest.mark.usefixtures('db')
@pytest.mark.parametrize(('sender_email', 'result'), (
    ('Foo <foo@example.com>', ('Foo <foo@example.com>', set())),
    ('Bar <bar@specific.com>', ('Bar <bar@specific.com>', set())),
    ('', ('Indico <noreply@example.com>', set())),
))
def test_smtp_sender_config_notset(mocker, sender_email, result):
    mocker.patch('indico.core.emails.config', SMTPSenderNotSetMockConfig())
    core_settings.set('site_title', 'Indico')
    assert get_actual_sender_address(sender_email, set()) == result
    assert get_actual_sender_address(sender_email, {'reply@whatever.com'}) == (result[0], {'reply@whatever.com'})
