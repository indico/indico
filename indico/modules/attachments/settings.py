# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from enum import auto

from indico.core.settings.converters import EnumConverter
from indico.modules.events.settings import EventSettingsProxy
from indico.util.enum import RichStrEnum
from indico.util.i18n import _


class AttachmentPackageAccess(RichStrEnum):
    __titles__ = {
        'everyone': _('Everyone'),
        'logged_in': _('Logged-in users'),
        'managers': _('Event managers'),
    }
    everyone = auto()
    logged_in = auto()
    managers = auto()


attachments_settings = EventSettingsProxy('attachments', {
    # Whether only managers can upload attachments
    'managers_only': False,
    # Who can generate attachment packages
    'generate_package': AttachmentPackageAccess.managers,
}, converters={
    'generate_package': EnumConverter(AttachmentPackageAccess),
})
