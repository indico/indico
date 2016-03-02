# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.util.event import unify_event_args
from indico.util.i18n import _
from indico.util.struct.iterables import materialize_iterable
from indico.util.user import unify_user_args


@unify_user_args
@unify_event_args(legacy=True)
def can_lock(event, user):
    """Checks whether a user can lock/unlock an event."""
    if not user:
        return False
    elif user.is_admin:
        return True
    elif user == event.as_event.creator:
        return True
    else:
        return any(cat.canUserModify(user.as_avatar) for cat in event.getOwnerList())


class _ProtectedObjectWrapper(object):
    def __init__(self, obj):
        self.object = obj

    @property
    def title(self):
        return self.object.title

    @property
    def is_public(self):
        return self.object.is_public

    @property
    def type_name(self):
        if isinstance(self.object, db.m.Event):
            return _('Event')
        elif isinstance(self.object, db.m.Session):
            return _('Session')
        elif isinstance(self.object, db.m.Contribution):
            return _('Contribution')
        elif isinstance(self.object, db.m.SubContribution):
            return _('Subcontribution')
        elif isinstance(self.object, db.m.AttachmentFolder):
            return _('Folder')
        elif isinstance(self.object, db.m.Attachment):
            return _('File')
        else:
            raise TypeError('Unexpected object of type {}: {}'.format(type(self.object).__name__, self.object))

    def __repr__(self):
        return '<_ProtectedObjectWrapper({})>'.format(self.object)


@materialize_iterable(set)
def get_non_inheriting_objects(root):
    """Get a set of child objects that do not inherit protection

    :param root: An event object (`Event`, `Session`, `Contribution`
                 or `AttachmentFolder`) which may contain objects
                 with a different protection.
    """
    def _query_folders(obj, crit):
        return (db.m.AttachmentFolder.query
                .filter_by(event_new=obj.event_new, is_deleted=False)
                .filter(crit)
                .options(joinedload('attachments')))

    def _process_attachments(folders):
        for folder in folders:
            if not folder.is_inheriting:
                yield folder
            for attachment in folder.attachments:
                if not attachment.is_inheriting:
                    yield attachment

    if isinstance(root, db.m.Event):
        # For an event we check sessions, contributions and ALL attachments no matter where
        for sess in root.sessions.filter(~db.m.Session.is_inheriting):
            yield _ProtectedObjectWrapper(sess)
        for contrib in root.contributions.filter(~db.m.Contribution.is_inheriting):
            yield _ProtectedObjectWrapper(contrib)
        query = (root.all_attachment_folders
                 .filter_by(is_deleted=False)
                 .options(joinedload('attachments')))
        for obj in _process_attachments(query):
            yield _ProtectedObjectWrapper(obj)

    elif isinstance(root, db.m.Session):
        # For a session we check contributions and attachments within the session
        crit = db.or_(
            # attached to the session
            db.m.AttachmentFolder.object == root,
            # attached to a contribution in the session
            db.and_(
                db.m.AttachmentFolder.link_type == LinkType.contribution,
                db.m.AttachmentFolder.contribution.has(
                    db.and_(
                        db.m.Contribution.session == root,
                        ~db.m.Contribution.is_deleted
                    )
                )
            ),
            # attached to a subcontribution in a contribution in the session
            db.and_(
                db.m.AttachmentFolder.link_type == LinkType.subcontribution,
                db.m.AttachmentFolder.subcontribution.has(
                    db.and_(
                        ~db.m.SubContribution.is_deleted,
                        db.m.SubContribution.contribution.has(
                            db.and_(
                                db.m.Contribution.session == root,
                                ~db.m.Contribution.is_deleted
                            )
                        )
                    )
                )
            )
        )
        for obj in _process_attachments(_query_folders(root, crit)):
            yield _ProtectedObjectWrapper(obj)
        for contrib in root.contributions:
            if not contrib.is_inheriting:
                yield _ProtectedObjectWrapper(contrib)

    elif isinstance(root, db.m.Contribution):
        # For a contribution we check attachments and subcontrib attachments
        crit = db.or_(
            # attached to the contribution
            db.m.AttachmentFolder.object == root,
            # attached to a subcontribution of the contribution
            db.and_(
                db.m.AttachmentFolder.link_type == LinkType.subcontribution,
                db.m.AttachmentFolder.subcontribution.has(
                    db.and_(
                        db.m.SubContribution.contribution == root,
                        ~db.m.SubContribution.is_deleted
                    )
                )
            )
        )
        for obj in _process_attachments(_query_folders(root, crit)):
            yield _ProtectedObjectWrapper(obj)

    elif isinstance(root, db.m.AttachmentFolder):
        # For an attachment folder we only check attachments in there
        for attachment in root.attachments:
            if not attachment.is_inheriting:
                yield _ProtectedObjectWrapper(attachment)

    else:
        raise TypeError('Unexpected object of type {}: {}'.format(type(root).__name__, root))
