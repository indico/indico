# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from smtplib import SMTP

import pytest


@pytest.fixture(autouse=True)
def disallow_emails(monkeypatch):
    """Prevent any code from connecting to a SMTP server.

    Return a set where you can add `(host, port)` combinations that
    should be exempt from the SMTP restriction.
    """

    orig_connect = SMTP.connect
    allowed = set()

    def _connect(self, host='localhost', port=0):
        if (host, port) in allowed:
            return orig_connect(self, host, port)
        __tracebackhide__ = True
        pytest.fail('Code tried to send an email unexpectedly')

    def _emit(*args, **kwargs):
        __tracebackhide__ = True
        pytest.fail('Logger tried to send an email')

    monkeypatch.setattr(SMTP, 'connect', _connect)
    monkeypatch.setattr('logging.handlers.SMTPHandler.emit', _emit)
    return allowed
