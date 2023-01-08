# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.core.emails import _rewrite_sender
from indico.vendor.django_mail.message import EmailMessage


class MockConfig:
    SMTP_ALLOWED_SENDERS = {'*@example.com', 'foo@specific.com'}
    SMTP_SENDER_FALLBACK = 'noreply@example.com'


@pytest.mark.parametrize('with_name', (False, True))
@pytest.mark.parametrize(('from_email', 'sender'), (
    ('foo@example.com', 'foo@example.com'),
    ('bar@example.com', 'bar@example.com'),
    ('test@specific.com', 'noreply@example.com'),
    ('foo@specific.com', 'foo@specific.com'),
))
def test_rewrite_sender(mocker, with_name, from_email, sender):
    mocker.patch('indico.core.emails.config', MockConfig())
    if with_name:
        if from_email == sender:
            # this is a bit ugly, but if we have no rewriting to the fallback,
            # we need to inject the name in the expected sender address
            sender = f'Spammer <{sender}>'
        from_email = f'Spammer <{from_email}>'
    msg = EmailMessage(from_email=from_email)
    _rewrite_sender(msg)
    assert msg.from_email == sender
    assert msg.message()['From'] == from_email


def test_rewrite_sender_notset():
    msg = EmailMessage(from_email='foo@example.com')
    _rewrite_sender(msg)
    assert msg.from_email == 'foo@example.com'
    assert msg.message()['From'] == 'foo@example.com'
