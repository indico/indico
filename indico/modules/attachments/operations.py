# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.core.permissions import update_read_permissions
from indico.modules.attachments import logger
from indico.modules.attachments.models.attachments import Attachment, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder


def add_attachment_link(form, linked_object):
    """Add a link attachment to linked_object."""
    form_data = form.data
    folder = form_data.pop('folder', None)
    if not folder:
        folder = AttachmentFolder.get_or_create_default(linked_object=linked_object)
    assert folder.object == linked_object
    link = Attachment(user=session.user, type=AttachmentType.link, folder=folder)
    link.populate_from_dict(form_data, skip={'acl', 'protected'})
    db.session.flush()
    # To be able to log attachment ID these steps must be done after flushing
    if link.is_self_protected and 'acl' in form_data:
        update_read_permissions(link, form)
    logger.info('Attachment %s added by %s', link, session.user)
    signals.attachments.attachment_created.send(link, user=session.user)
