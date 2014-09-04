## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

import pytest


@pytest.fixture(autouse=True)
def disallow_emails(monkeypatch):
    """Prevents any code from connecting to a SMTP server"""

    def _fail(*args, **kwargs):
        pytest.fail('Code tried to send an email unexpectedly')

    monkeypatch.setattr('smtplib.SMTP.connect', _fail)
    monkeypatch.setattr('logging.handlers.SMTPHandler.emit', _fail)


@pytest.fixture(autouse=True)
def disallow_zodb(monkeypatch):
    """Prevents any code from connecting to ZODB"""

    @staticmethod
    def _fail(*args, **kwargs):
        __tracebackhide__ = True
        pytest.fail('Code tried to connect to ZODB')

    monkeypatch.setattr('indico.core.db.manager.DBMgr.getInstance', _fail)
