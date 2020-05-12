# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import mimetypes
import os
import random
import time
from cStringIO import StringIO
from email import charset as Charset
from email import encoders as Encoders
from email import generator, message_from_string
from email.header import Header
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.message import MIMEMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, getaddresses, parseaddr

from speaklater import is_lazy_string
from werkzeug.urls import url_parse

from indico.util.string import to_unicode


def force_text(val):
    if is_lazy_string(val):
        val = val.value
    return to_unicode(val)


# The following code is taken almost verbatim from `django.core.mail`,
# which is licensed under the three-clause BSD license and is originally
# available on the following URL:
# https://github.com/django/django/tree/stable/1.11.x/django/core/mail/
# Credits of the original code go to the Django Software Foundation
# and their contributors.


# Don't BASE64-encode UTF-8 messages so that we avoid unwanted attention from
# some spam filters.

utf8_charset = Charset.Charset('utf-8')
utf8_charset.body_encoding = None  # Python defaults to BASE64
utf8_charset_qp = Charset.Charset('utf-8')
utf8_charset_qp.body_encoding = Charset.QP

# Default MIME type to use on attachments (if it is not explicitly given
# and cannot be guessed).
DEFAULT_ATTACHMENT_MIME_TYPE = 'application/octet-stream'

RFC5322_EMAIL_LINE_LENGTH_LIMIT = 998


class BadHeaderError(ValueError):
    pass


# Copied from Python 3.2+ standard library, with the following modification:
# * Uses hostname from indico's BASE_URL as the default domain
def make_msgid(idstring=None, domain=None):
    """Returns a string suitable for RFC 2822 compliant Message-ID, e.g:

    <142480216486.20800.16526388040877946887@nightshade.la.mastaler.com>

    Optional idstring if given is a string used to strengthen the
    uniqueness of the message id.  Optional domain if given provides the
    portion of the message id after the '@'.  It defaults to the locally
    defined hostname.
    """
    from indico.core.config import config
    timeval = int(time.time() * 100)
    pid = os.getpid()
    randint = random.getrandbits(64)
    if idstring is None:
        idstring = ''
    else:
        idstring = '.' + idstring
    if domain is None:
        domain = url_parse(config.BASE_URL).host
    return '<%d.%d.%d%s@%s>' % (timeval, pid, randint, idstring, domain)


# Header names that contain structured address data (RFC #5322)
ADDRESS_HEADERS = {
    'from',
    'sender',
    'reply-to',
    'to',
    'cc',
    'bcc',
    'resent-from',
    'resent-sender',
    'resent-to',
    'resent-cc',
    'resent-bcc',
}


def forbid_multi_line_headers(name, val, encoding):
    """Forbids multi-line headers, to prevent header injection."""
    val = force_text(val)
    if '\n' in val or '\r' in val:
        raise BadHeaderError("Header values can't contain newlines (got %r for header %r)" % (val, name))
    try:
        val.encode('ascii')
    except UnicodeEncodeError:
        if name.lower() in ADDRESS_HEADERS:
            val = ', '.join(sanitize_address(addr, encoding) for addr in getaddresses((val,)))
        else:
            val = Header(val, encoding).encode()
    else:
        if name.lower() == 'subject':
            val = Header(val).encode()
    return str(name), val


def split_addr(addr, encoding):
    """
    Split the address into local part and domain, properly encoded.

    When non-ascii characters are present in the local part, it must be
    MIME-word encoded. The domain name must be idna-encoded if it contains
    non-ascii characters.
    """
    if '@' in addr:
        localpart, domain = addr.split('@', 1)
        # Try to get the simplest encoding - ascii if possible so that
        # to@example.com doesn't become =?utf-8?q?to?=@example.com. This
        # makes unit testing a bit easier and more readable.
        try:
            localpart.encode('ascii')
        except UnicodeEncodeError:
            localpart = Header(localpart, encoding).encode()
        domain = domain.encode('idna').decode('ascii')
    else:
        localpart = Header(addr, encoding).encode()
        domain = ''
    return localpart, domain


def sanitize_address(addr, encoding):
    """
    Format a pair of (name, address) or an email address string.
    """
    if not isinstance(addr, tuple):
        addr = parseaddr(force_text(addr))
    nm, addr = addr
    localpart, domain = None, None
    nm = Header(nm, encoding).encode()
    try:
        addr.encode('ascii')
    except UnicodeEncodeError:  # IDN or non-ascii in the local part
        localpart, domain = split_addr(addr, encoding)

    # On Python 2, use the stdlib since `email.headerregistry` doesn't exist.
    if localpart and domain:
        addr = '@'.join([localpart, domain])
    return formataddr((nm, addr))


class MIMEMixin:
    def as_string(self, unixfrom=False, linesep='\n'):
        """Return the entire formatted message as a string.
        Optional `unixfrom' when True, means include the Unix From_ envelope
        header.

        This overrides the default as_string() implementation to not mangle
        lines that begin with 'From '. See bug #13433 for details.
        """
        fp = StringIO()
        g = generator.Generator(fp, mangle_from_=False)
        g.flatten(self, unixfrom=unixfrom)
        return fp.getvalue()

    as_bytes = as_string


class SafeMIMEMessage(MIMEMixin, MIMEMessage):
    def __setitem__(self, name, val):
        # message/rfc822 attachments must be ASCII
        name, val = forbid_multi_line_headers(name, val, 'ascii')
        MIMEMessage.__setitem__(self, name, val)


class SafeMIMEText(MIMEMixin, MIMEText):
    def __init__(self, _text, _subtype='plain', _charset=None):
        self.encoding = _charset
        MIMEText.__init__(self, _text, _subtype=_subtype, _charset=_charset)

    def __setitem__(self, name, val):
        name, val = forbid_multi_line_headers(name, val, self.encoding)
        MIMEText.__setitem__(self, name, val)

    def set_payload(self, payload, charset=None):
        if charset == 'utf-8':
            has_long_lines = any(
                len(line.encode('utf-8')) > RFC5322_EMAIL_LINE_LENGTH_LIMIT
                for line in payload.splitlines()
            )
            # Quoted-Printable encoding has the side effect of shortening long
            # lines, if any (#22561).
            charset = utf8_charset_qp if has_long_lines else utf8_charset
        MIMEText.set_payload(self, payload, charset=charset)


class SafeMIMEMultipart(MIMEMixin, MIMEMultipart):
    def __init__(self, _subtype='mixed', boundary=None, _subparts=None, encoding=None, **_params):
        self.encoding = encoding
        MIMEMultipart.__init__(self, _subtype, boundary, _subparts, **_params)

    def __setitem__(self, name, val):
        name, val = forbid_multi_line_headers(name, val, self.encoding)
        MIMEMultipart.__setitem__(self, name, val)


class EmailMessage(object):
    """
    A container for email information.
    """
    content_subtype = 'plain'
    mixed_subtype = 'mixed'
    encoding = 'utf-8'

    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
                 connection=None, attachments=None, headers=None, cc=None,
                 reply_to=None):
        """
        Initialize a single email message (which can be sent to multiple
        recipients).

        All strings used to create the message can be unicode strings
        (or UTF-8 bytestrings). The SafeMIMEText class will handle any
        necessary encoding conversions.
        """
        if to:
            if isinstance(to, basestring):
                raise TypeError('"to" argument must be a list or tuple')
            self.to = list(to)
        else:
            self.to = []
        if cc:
            if isinstance(cc, basestring):
                raise TypeError('"cc" argument must be a list or tuple')
            self.cc = list(cc)
        else:
            self.cc = []
        if bcc:
            if isinstance(bcc, basestring):
                raise TypeError('"bcc" argument must be a list or tuple')
            self.bcc = list(bcc)
        else:
            self.bcc = []
        if reply_to:
            if isinstance(reply_to, basestring):
                raise TypeError('"reply_to" argument must be a list or tuple')
            self.reply_to = list(reply_to)
        else:
            self.reply_to = []
        self.from_email = from_email
        self.subject = subject
        self.body = body
        self.attachments = []
        if attachments:
            for attachment in attachments:
                if isinstance(attachment, MIMEBase):
                    self.attach(attachment)
                else:
                    self.attach(*attachment)
        self.extra_headers = headers or {}
        self.connection = connection

    def get_connection(self, fail_silently=False):
        from indico.util.emails.backend import EmailBackend
        if not self.connection:
            return EmailBackend(fail_silently=fail_silently)
        return self.connection

    def message(self):
        msg = SafeMIMEText(self.body, self.content_subtype, self.encoding)
        msg = self._create_message(msg)
        msg['Subject'] = self.subject
        msg['From'] = self.extra_headers.get('From', self.from_email)
        msg['To'] = self.extra_headers.get('To', ', '.join(map(force_text, self.to)))
        if self.cc:
            msg['Cc'] = ', '.join(map(force_text, self.cc))
        if self.reply_to:
            msg['Reply-To'] = self.extra_headers.get('Reply-To', ', '.join(map(force_text, self.reply_to)))

        # Email header names are case-insensitive (RFC 2045), so we have to
        # accommodate that when doing comparisons.
        header_names = [key.lower() for key in self.extra_headers]
        if 'date' not in header_names:
            # formatdate() uses stdlib methods to format the date, which use
            # the stdlib/OS concept of a timezone, however, Django sets the
            # TZ environment variable based on the TIME_ZONE setting which
            # will get picked up by formatdate().
            msg['Date'] = formatdate()
        if 'message-id' not in header_names:
            msg['Message-ID'] = make_msgid()
        for name, value in self.extra_headers.items():
            if name.lower() in ('from', 'to'):  # From and To are already handled
                continue
            msg[name] = value
        return msg

    def recipients(self):
        """
        Returns a list of all recipients of the email (includes direct
        addressees as well as Cc and Bcc entries).
        """
        return [email for email in (self.to + self.cc + self.bcc) if email]

    def send(self, fail_silently=False):
        """Sends the email message."""
        if not self.recipients():
            # Don't bother creating the network connection if there's nobody to
            # send to.
            return 0
        return self.get_connection(fail_silently).send_messages([self])

    def attach(self, filename=None, content=None, mimetype=None):
        """
        Attaches a file with the given filename and content. The filename can
        be omitted and the mimetype is guessed, if not provided.

        If the first parameter is a MIMEBase subclass it is inserted directly
        into the resulting message attachments.

        For a text/* mimetype (guessed or specified), when a bytes object is
        specified as content, it will be decoded as UTF-8. If that fails,
        the mimetype will be set to DEFAULT_ATTACHMENT_MIME_TYPE and the
        content is not decoded.
        """
        if isinstance(filename, MIMEBase):
            assert content is None
            assert mimetype is None
            self.attachments.append(filename)
        else:
            assert content is not None

            if not mimetype:
                mimetype, _ = mimetypes.guess_type(filename)
                if not mimetype:
                    mimetype = DEFAULT_ATTACHMENT_MIME_TYPE
            basetype, subtype = mimetype.split('/', 1)

            if basetype == 'text':
                if isinstance(content, str):
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        # If mimetype suggests the file is text but it's actually
                        # binary, read() will raise a UnicodeDecodeError on Python 3.
                        mimetype = DEFAULT_ATTACHMENT_MIME_TYPE

            self.attachments.append((filename, content, mimetype))

    def attach_file(self, path, mimetype=None):
        """
        Attaches a file from the filesystem.

        The mimetype will be set to the DEFAULT_ATTACHMENT_MIME_TYPE if it is
        not specified and cannot be guessed.

        For a text/* mimetype (guessed or specified), the file's content
        will be decoded as UTF-8. If that fails, the mimetype will be set to
        DEFAULT_ATTACHMENT_MIME_TYPE and the content is not decoded.
        """
        filename = os.path.basename(path)

        with open(path, 'rb') as file:
            content = file.read()
            self.attach(filename, content, mimetype)

    def _create_message(self, msg):
        return self._create_attachments(msg)

    def _create_attachments(self, msg):
        if self.attachments:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.mixed_subtype, encoding=self.encoding)
            if self.body:
                msg.attach(body_msg)
            for attachment in self.attachments:
                if isinstance(attachment, MIMEBase):
                    msg.attach(attachment)
                else:
                    msg.attach(self._create_attachment(*attachment))
        return msg

    def _create_mime_attachment(self, content, mimetype):
        """
        Converts the content, mimetype pair into a MIME attachment object.

        If the mimetype is message/rfc822, content may be an
        email.Message or EmailMessage object, as well as a str.
        """
        basetype, subtype = mimetype.split('/', 1)
        if basetype == 'text':
            attachment = SafeMIMEText(content, subtype, self.encoding)
        elif basetype == 'message' and subtype == 'rfc822':
            # Bug #18967: per RFC2046 s5.2.1, message/rfc822 attachments
            # must not be base64 encoded.
            if isinstance(content, EmailMessage):
                # convert content into an email.Message first
                content = content.message()
            elif not isinstance(content, Message):
                # For compatibility with existing code, parse the message
                # into an email.Message object if it is not one already.
                content = message_from_string(content)

            attachment = SafeMIMEMessage(content, subtype)
        else:
            # Encode non-text attachments with base64.
            attachment = MIMEBase(basetype, subtype)
            attachment.set_payload(content)
            Encoders.encode_base64(attachment)
        return attachment

    def _create_attachment(self, filename, content, mimetype=None):
        """
        Converts the filename, content, mimetype triple into a MIME attachment
        object.
        """
        attachment = self._create_mime_attachment(content, mimetype)
        if filename:
            try:
                filename.encode('ascii')
            except UnicodeEncodeError:
                filename = filename.encode('utf-8')
                filename = ('utf-8', '', filename)
            attachment.add_header('Content-Disposition', 'attachment',
                                  filename=filename)
        return attachment


class EmailMultiAlternatives(EmailMessage):
    """
    A version of EmailMessage that makes it easy to send multipart/alternative
    messages. For example, including text and HTML versions of the text is
    made easier.
    """
    alternative_subtype = 'alternative'

    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
                 connection=None, attachments=None, headers=None, alternatives=None,
                 cc=None, reply_to=None):
        """
        Initialize a single email message (which can be sent to multiple
        recipients).

        All strings used to create the message can be unicode strings (or UTF-8
        bytestrings). The SafeMIMEText class will handle any necessary encoding
        conversions.
        """
        super(EmailMultiAlternatives, self).__init__(
            subject, body, from_email, to, bcc, connection, attachments,
            headers, cc, reply_to,
        )
        self.alternatives = alternatives or []

    def attach_alternative(self, content, mimetype):
        """Attach an alternative content representation."""
        assert content is not None
        assert mimetype is not None
        self.alternatives.append((content, mimetype))

    def _create_message(self, msg):
        return self._create_attachments(self._create_alternatives(msg))

    def _create_alternatives(self, msg):
        if self.alternatives:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.alternative_subtype, encoding=self.encoding)
            if self.body:
                msg.attach(body_msg)
            for alternative in self.alternatives:
                msg.attach(self._create_mime_attachment(*alternative))
        return msg
