# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from smtplib import SMTP

import pytest


@pytest.fixture(autouse=True)
def disallow_emails(monkeypatch):
    """Prevents any code from connecting to a SMTP server.

    Returns a set where you can add `(host, port)` combinations that
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
