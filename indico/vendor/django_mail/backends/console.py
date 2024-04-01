# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# The code in here is taken almost verbatim from `django.core.mail.backends.console`,
# which is licensed under the three-clause BSD license and is originally
# available on the following URL:
# https://github.com/django/django/blob/425b26092f/django/core/mail/backends/console.py
# Credits of the original code go to the Django Software Foundation
# and their contributors.

"""
Email backend that writes messages to console instead of sending them.
"""
import sys
import threading

from .base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    def __init__(self, *args, **kwargs):
        self.stream = kwargs.pop('stream', sys.stdout)
        self._lock = threading.RLock()
        super().__init__(*args, **kwargs)

    def write_message(self, message):
        msg = message.message()
        msg_data = msg.as_bytes()
        charset = (
            msg.get_charset().get_output_charset() if msg.get_charset() else 'utf-8'
        )
        msg_data = msg_data.decode(charset)
        self.stream.write('%s\n' % msg_data)
        self.stream.write('-' * 79)
        self.stream.write('\n')

    def send_messages(self, email_messages):
        """Write all messages to the stream in a thread-safe way."""
        if not email_messages:
            return
        msg_count = 0
        with self._lock:
            try:
                stream_created = self.open()
                for message in email_messages:
                    self.write_message(message)
                    self.stream.flush()  # flush after each message
                    msg_count += 1
                if stream_created:
                    self.close()
            except Exception:
                if not self.fail_silently:
                    raise
        return msg_count
