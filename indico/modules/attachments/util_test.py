# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.attachments.settings import AttachmentPackageAccess, attachments_settings
from indico.modules.attachments.util import can_generate_attachment_package


def test_can_generate_attachment_package(dummy_user, create_user, dummy_event):
    manager = dummy_user
    user = create_user(123)
    dummy_event.update_principal(manager, full_access=True)

    # default: only managers
    assert attachments_settings.get(dummy_event, 'generate_package') == AttachmentPackageAccess.managers
    assert can_generate_attachment_package(dummy_event, manager)
    assert not can_generate_attachment_package(dummy_event, user)
    assert not can_generate_attachment_package(dummy_event, None)
    # logged-in users
    attachments_settings.set(dummy_event, 'generate_package', AttachmentPackageAccess.logged_in)
    assert can_generate_attachment_package(dummy_event, manager)
    assert can_generate_attachment_package(dummy_event, user)
    assert not can_generate_attachment_package(dummy_event, None)
    # everyone
    attachments_settings.set(dummy_event, 'generate_package', AttachmentPackageAccess.everyone)
    assert can_generate_attachment_package(dummy_event, manager)
    assert can_generate_attachment_package(dummy_event, user)
    assert can_generate_attachment_package(dummy_event, None)
