# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# The code in here is taken almost verbatim from `django.core.mail.backends.locmem`,
# which is licensed under the three-clause BSD license and is originally
# available on the following URL:
# https://github.com/django/django/blob/425b26092f/django/core/mail/backends/locmem.py
# Credits of the original code go to the Django Software Foundation
# and their contributors.

"""
Backend for test environment.
"""

import copy

from indico.vendor import django_mail

from .base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    """
    An email backend for use during test sessions.

    The test connection stores email messages in a dummy outbox,
    rather than sending them out on the wire.

    The dummy outbox is accessible through the outbox instance attribute.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(django_mail, 'outbox'):
            django_mail.outbox = []

    def send_messages(self, messages):
        """Redirect messages to the dummy outbox"""
        msg_count = 0
        for message in messages:  # .message() triggers header validation
            message.message()
            django_mail.outbox.append(copy.deepcopy(message))
            msg_count += 1
        return msg_count
