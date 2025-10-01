# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.util.i18n import _
from indico.util.placeholders import Placeholder


class RecipientFirstNamePlaceholder(Placeholder):
    name = 'first_name'
    description = _('First name of the recipient')

    @classmethod
    def render(cls, recipient, **kwargs):
        return recipient.first_name


class RecipientLastNamePlaceholder(Placeholder):
    name = 'last_name'
    description = _('Last name of the recipient')

    @classmethod
    def render(cls, recipient, **kwargs):
        return recipient.last_name
