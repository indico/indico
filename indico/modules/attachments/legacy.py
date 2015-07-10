# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from persistent import Persistent

from indico.modules.attachments.models.attachments import Attachment
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments import signals
from indico.util.fossilize import IFossil, fossilizes
from indico.web.flask.util import url_for


def connect_legacy_signals():
    signals.attachments.folder_updated.connect(_folder_updated)
    signals.attachments.folder_deleted.connect(_folder_deleted)
    signals.attachments.attachment_created.connect(_attachment_changed)
    signals.attachments.attachment_updated.connect(_attachment_changed)
    signals.attachments.attachment_deleted.connect(_attachment_deleted)


class AccessControllerAdapter(object):
    def __init__(self, obj):
        self.obj = obj.as_new

    def getAccessProtectionLevel(self):
        return int(self.obj.is_protected)


class IWrapperFossil(IFossil):
    def getId():
        pass

    def title():
        pass

    def getProtectionURL():
        pass
    getProtectionURL.produce = lambda obj: url_for('attachments.management', obj.linked_object)


class Wrapper(Persistent):
    """
    Very simple wrapper around Attachment/AttachmentFolder
    that allows them to be stored in obj.nonInheritingChildren
    """

    fossilizes(IWrapperFossil)

    def __init__(self, obj):
        self.id = obj.id

    def getId(self):
        return self.id

    @property
    def title(self):
        return self.as_new.title

    @property
    def as_new(self):
        return self.new_class.get(self.id)

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.id == other.id
        else:
            return False

    def __ne__(self, other):
        return not(self == other)

    def __hash__(self):
        return hash((self.__class__.__name__, self.id))

    def getAccessController(self):
        return AccessControllerAdapter(self)


class AttachmentWrapper(Wrapper):
    new_class = Attachment

    @property
    def linked_object(self):
        return self.as_new.folder.linked_object


class FolderWrapper(Wrapper):
    new_class = AttachmentFolder

    @property
    def linked_object(self):
        return self.as_new.linked_object


def _folder_updated(folder, **kwargs):
    folder.linked_object.updateNonInheritingChildren(FolderWrapper(folder))


def _folder_deleted(folder, **kwargs):
    obj = folder.linked_object
    obj.updateNonInheritingChildren(FolderWrapper(folder), delete=True)

    for attachment in folder.attachments:
        obj.updateNonInheritingChildren(AttachmentWrapper(attachment), delete=True)


def _attachment_changed(attachment, **kwargs):
    attachment.folder.linked_object.updateNonInheritingChildren(AttachmentWrapper(attachment))


def _attachment_deleted(attachment, **kwargs):
    attachment.folder.linked_object.updateNonInheritingChildren(AttachmentWrapper(attachment), delete=True)
