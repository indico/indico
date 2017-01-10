# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import pytest

from indico.core.config import Config


@pytest.yield_fixture
def smtp(disallow_emails, smtpserver):
    """Wrapper for the `smtpserver` fixture which updates the Indico config
    and disables the SMTP autofail logic for that smtp server.
    """
    old_smtp_server = Config.getInstance().getSmtpServer()
    Config.getInstance().update(SmtpServer=smtpserver.addr)
    disallow_emails.add(smtpserver.addr)  # whitelist our smtp server
    yield smtpserver
    Config.getInstance().update(SmtpServer=old_smtp_server)
