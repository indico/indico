# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest


@pytest.fixture
def smtp(disallow_emails, smtpserver, app):
    """Wrapper for the `smtpserver` fixture which updates the Indico config
    and disables the SMTP autofail logic for that smtp server.
    """
    old_email_host = app.config['EMAIL_HOST']
    old_email_port = app.config['EMAIL_PORT']
    app.config['EMAIL_HOST'] = smtpserver.addr[0]
    app.config['EMAIL_PORT'] = smtpserver.addr[1]
    disallow_emails.add(smtpserver.addr[:2])  # whitelist our smtp server
    yield smtpserver
    app.config['EMAIL_HOST'] = old_email_host
    app.config['EMAIL_PORT'] = old_email_port
