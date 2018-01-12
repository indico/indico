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

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.attachments import logger
from indico.modules.attachments.models.attachments import Attachment, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder


def add_attachment_link(data, linked_object):
    """Add a link attachment to linked_object"""
    folder = data.pop('folder', None)
    if not folder:
        folder = AttachmentFolder.get_or_create_default(linked_object=linked_object)
    assert folder.object == linked_object
    link = Attachment(user=session.user, type=AttachmentType.link, folder=folder)
    link.populate_from_dict(data, skip={'acl', 'protected'})
    if link.is_self_protected:
        link.acl = data['acl']
    db.session.flush()
    logger.info('Attachment %s added by %s', link, session.user)
    signals.attachments.attachment_created.send(link, user=session.user)
