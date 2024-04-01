# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# TODO: Move this whole package into a standalone pypi package, since it's
# useful in general for anyoen who wants to send emails (without using django)

# The code in here is taken almost verbatim from `django.core.mail`,
# which is licensed under the three-clause BSD license and is originally
# available on the following URL:
# https://github.com/django/django/blob/425b26092f/django/core/mail/__init__.py
# Credits of the original code go to the Django Software Foundation
# and their contributors.

"""
Tools for sending email.
"""
from flask import current_app

from .backends.base import BaseEmailBackend
from .module_loading_utils import import_string


__all__ = ['get_connection']


def get_connection(backend=None, fail_silently=False, **kwds) -> BaseEmailBackend:
    """Load an email backend and return an instance of it.

    If backend is None (default), use ``EMAIL_BACKEND`` from config.

    Both fail_silently and other keyword arguments are used in the
    constructor of the backend.
    """
    klass = import_string(backend or current_app.config['EMAIL_BACKEND'])
    return klass(fail_silently=fail_silently, **kwds)
