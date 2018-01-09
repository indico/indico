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

from __future__ import unicode_literals

import smtplib
import socket
import ssl
import threading

from indico.util.emails.message import sanitize_address


# The following code is taken almost verbatim from `django.core.mail`,
# which is licensed under the three-clause BSD license and is originally
# available on the following URL:
# https://github.com/django/django/tree/stable/1.11.x/django/core/mail/
# Credits of the original code go to the Django Software Foundation
# and their contributors.


class BaseEmailBackend(object):
    """
    Base class for email backend implementations.

    Subclasses must at least overwrite send_messages().

    open() and close() can be called indirectly by using a backend object as a
    context manager:

        with backend as connection:
            # do something with connection
            pass
    """
    def __init__(self, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently

    def open(self):
        """Open a network connection.

        This method can be overwritten by backend implementations to
        open a network connection.

        It's up to the backend implementation to track the status of
        a network connection if it's needed by the backend.

        This method can be called by applications to force a single
        network connection to be used when sending mails. See the
        send_messages() method of the SMTP backend for a reference
        implementation.

        The default implementation does nothing.
        """
        pass

    def close(self):
        """Close a network connection."""
        pass

    def __enter__(self):
        try:
            self.open()
        except Exception:
            self.close()
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects and returns the number of email
        messages sent.
        """
        raise NotImplementedError('subclasses of BaseEmailBackend must override send_messages() method')


class EmailBackend(BaseEmailBackend):
    """
    A wrapper that manages the SMTP network connection.
    """
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=False, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None,
                 **kwargs):
        from indico.core.config import config
        super(EmailBackend, self).__init__(fail_silently=fail_silently)
        self.host = host or config.SMTP_SERVER[0]
        self.port = port or config.SMTP_SERVER[1]
        self.username = config.SMTP_LOGIN if username is None else username
        self.password = config.SMTP_PASSWORD if password is None else password
        self.use_tls = config.SMTP_USE_TLS if use_tls is None else use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile
        if self.use_ssl and self.use_tls:
            raise ValueError(
                "use_ssl/use_tls are mutually exclusive, so only set "
                "one of those settings to True.")
        self.connection = None
        self._lock = threading.RLock()

    @property
    def connection_class(self):
        return smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP

    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a
        new connection was required (True or False) or None if an exception
        passed silently.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False

        connection_params = {}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        if self.use_ssl:
            connection_params.update({
                'keyfile': self.ssl_keyfile,
                'certfile': self.ssl_certfile,
            })
        try:
            self.connection = self.connection_class(self.host, self.port, **connection_params)

            # TLS/SSL are mutually exclusive, so only attempt TLS over
            # non-secure connections.
            if not self.use_ssl and self.use_tls:
                self.connection.starttls(keyfile=self.ssl_keyfile, certfile=self.ssl_certfile)
            if self.username and self.password:
                self.connection.login(str(self.username), str(self.password))
            return True
        except (smtplib.SMTPException, socket.error):
            if not self.fail_silently:
                raise

    def close(self):
        """Closes the connection to the email server."""
        if self.connection is None:
            return
        try:
            try:
                self.connection.quit()
            except (ssl.SSLError, smtplib.SMTPServerDisconnected):
                # This happens when calling quit() on a TLS connection
                # sometimes, or when the connection was already disconnected
                # by the server.
                self.connection.close()
            except smtplib.SMTPException:
                if self.fail_silently:
                    return
                raise
        finally:
            self.connection = None

    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects and returns the number of email
        messages sent.
        """
        if not email_messages:
            return
        with self._lock:
            new_conn_created = self.open()
            if not self.connection or new_conn_created is None:
                # We failed silently on open().
                # Trying to send would be pointless.
                return
            num_sent = 0
            for message in email_messages:
                sent = self._send(message)
                if sent:
                    num_sent += 1
            if new_conn_created:
                self.close()
        return num_sent

    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or 'utf-8'
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.message()
        try:
            self.connection.sendmail(from_email, recipients, message.as_bytes(linesep='\r\n'))
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False
        return True
