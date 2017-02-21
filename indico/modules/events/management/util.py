# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from contextlib import contextmanager

from flask import flash, session
from markupsafe import Markup, escape
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.util.i18n import _, ngettext
from indico.util.struct.iterables import materialize_iterable
from indico.web.flask.util import url_for


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
        if isinstance(self.object, db.m.Session):
            return _('Session')
        elif isinstance(self.object, db.m.Contribution):
            return _('Contribution')
        elif isinstance(self.object, db.m.AttachmentFolder):
            return _('Folder')
        elif isinstance(self.object, db.m.Attachment):
            return _('File')
        else:
            raise TypeError('Unexpected object of type {}: {}'.format(type(self.object).__name__, self.object))

    @property
    def edit_link_attrs(self):
        if isinstance(self.object, db.m.Session):
            return {'data-ajax-dialog': True,
                    'data-title': _('Edit session "{name}"').format(name=self.object.title),
                    'data-href': url_for('sessions.session_protection', self.object)}
        elif isinstance(self.object, db.m.Contribution):
            return {'data-ajax-dialog': True,
                    'data-title': _('Edit contribution "{name}"').format(name=self.object.title),
                    'data-href': url_for('contributions.manage_contrib_protection', self.object)}
        elif isinstance(self.object, db.m.AttachmentFolder):
            return {'data-ajax-dialog': True,
                    'data-title': _('Edit folder "{name}"').format(name=self.object.title),
                    'data-href': url_for('attachments.edit_folder', self.object)}
        elif isinstance(self.object, db.m.Attachment):
            return {'data-ajax-dialog': True,
                    'data-title': _('Edit attachment "{name}"').format(name=self.object.title),
                    'data-href': url_for('attachments.modify_attachment', self.object)}
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
        for sess in db.m.Session.query.with_parent(root).filter(~db.m.Session.is_inheriting):
            yield _ProtectedObjectWrapper(sess)
        for contrib in db.m.Contribution.query.with_parent(root).filter(~db.m.Contribution.is_inheriting):
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


@contextmanager
def flash_if_unregistered(event, get_person_links):
    """Flash message when adding users with no indico account

    :param event: Current event
    :param get_person_links: Callable returning list of person links to
                             check
    """
    old_non_users = {pl for pl in get_person_links() if pl.person.user is None}
    yield
    new_non_users = {pl for pl in get_person_links() if pl.person.user is None}
    added_non_users = len(new_non_users - old_non_users)
    if not added_non_users:
        return
    warning = ngettext('You have added a user with no Indico account.',
                       'You have added {} users with no Indico account.', added_non_users).format(added_non_users)
    msg = _('An Indico account may be needed to upload materials and/or manage contents.')
    if event.can_manage(session.user):
        continue_msg = (escape(_('To invite them, please go to the {link_start}Roles page{link_end}'))
                        .format(link_start=Markup('<a href="{}">').format(url_for('persons.person_list', event)),
                                link_end=Markup('</a>')))
    else:
        continue_msg = ngettext('Please contact the manager if you think this user should be able to access these '
                                'features.',
                                'Please contact the manager if you think these users should be able to access '
                                'these features.', added_non_users)
    flash(Markup(' ').join([warning, msg, continue_msg]), 'warning')
