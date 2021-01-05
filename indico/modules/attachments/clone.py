# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.orm import joinedload, subqueryload

from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.models.principals import AttachmentFolderPrincipal, AttachmentPrincipal
from indico.modules.events.cloning import EventCloner
from indico.util.i18n import _


class AttachmentCloner(EventCloner):
    name = 'attachments'
    friendly_name = _('Materials')
    uses = {'sessions', 'contributions', 'event_roles', 'registration_forms'}

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def has_conflicts(self, target_event):
        return self._has_content(target_event)

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._clone_nested_attachments = False
        self._event_role_map = self._session_map = self._contrib_map = self._subcontrib_map = self._regform_map = None
        if cloners >= {'sessions', 'contributions'}:
            self._clone_nested_attachments = True
            self._session_map = shared_data['sessions']['session_map']
            self._contrib_map = shared_data['contributions']['contrib_map']
            self._subcontrib_map = shared_data['contributions']['subcontrib_map']
        if 'event_roles' in cloners:
            self._event_role_map = shared_data['event_roles']['event_role_map']
        if 'registration_forms' in cloners:
            self._regform_map = shared_data['registration_forms']['form_map']
        with db.session.no_autoflush:
            self._clone_attachments(new_event)
        db.session.flush()

    def _has_content(self, event):
        return (event.all_attachment_folders
                .filter(~AttachmentFolder.is_deleted, AttachmentFolder.attachments.any(is_deleted=False))
                .has_rows())

    def _query_folders(self, base_query, for_event):
        query = (base_query
                 .filter_by(is_deleted=False)
                 .options(subqueryload('acl_entries'),
                          subqueryload('attachments').subqueryload('acl_entries')))
        if not for_event:
            query = (query
                     .options(joinedload('session'),
                              joinedload('contribution'),
                              joinedload('subcontribution'))
                     .filter(AttachmentFolder.link_type.in_([LinkType.session, LinkType.contribution,
                                                             LinkType.subcontribution])))
        return query

    def _clone_attachments(self, new_event):
        # event attachments
        for old_folder in self._query_folders(self.old_event.attachment_folders, True):
            self._clone_attachment_folder(old_folder, new_event)
        # session/contrib/subcontrib attachments
        if self._clone_nested_attachments:
            mapping = {LinkType.session: self._session_map,
                       LinkType.contribution: self._contrib_map,
                       LinkType.subcontribution: self._subcontrib_map}
            query = self._query_folders(self.old_event.all_attachment_folders, False)
            for old_folder in query:
                obj = old_folder.object
                if obj.is_deleted or (isinstance(obj, db.m.SubContribution) and obj.contribution.is_deleted):
                    continue
                self._clone_attachment_folder(old_folder, mapping[old_folder.link_type][obj])

    def _clone_attachment_folder(self, old_folder, new_object):
        folder_attrs = get_simple_column_attrs(AttachmentFolder)
        attachment_attrs = (get_simple_column_attrs(Attachment) | {'user'}) - {'modified_dt'}
        folder = AttachmentFolder(object=new_object)
        folder.populate_from_attrs(old_folder, folder_attrs)
        folder.acl_entries = clone_principals(AttachmentFolderPrincipal, old_folder.acl_entries,
                                              self._event_role_map, self._regform_map)
        for old_attachment in old_folder.attachments:
            attachment = Attachment(folder=folder)
            attachment.populate_from_attrs(old_attachment, attachment_attrs)
            attachment.acl_entries = clone_principals(AttachmentPrincipal, old_attachment.acl_entries,
                                                      self._event_role_map, self._regform_map)
            if attachment.type == AttachmentType.file:
                old_file = old_attachment.file
                attachment.file = AttachmentFile(attachment=attachment, user=old_file.user, filename=old_file.filename,
                                                 content_type=old_file.content_type)
                with old_file.open() as fd:
                    attachment.file.save(fd)
