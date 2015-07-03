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

from __future__ import unicode_literals

import mimetypes
import os
import sys
from itertools import chain
from operator import attrgetter
from uuid import uuid4

import click
from werkzeug.utils import secure_filename

from indico.core.db import db
from indico.core.config import Config
from indico.modules.attachments.models.attachments import Attachment, AttachmentType, AttachmentFile
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.models.legacy_mapping import LegacyAttachmentFolderMapping, LegacyAttachmentMapping
from indico.modules.attachments.models.principals import AttachmentPrincipal, AttachmentFolderPrincipal
from indico.modules.users import User
from indico.util.console import cformat, verbose_iterator
from indico.util.date_time import now_utc
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import protection_from_ac, patch_default_group_provider


class AttachmentImporter(Importer):
    def __init__(self, **kwargs):
        self.storage_backend = kwargs.pop('storage_backend')
        self.symlink_backend = kwargs.pop('symlink_backend')
        self.archive_dirs = kwargs.pop('archive_dir')
        self.default_group_provider = kwargs.pop('default_group_provider')
        self.avoid_storage_check = kwargs.pop('avoid_storage_check')
        self.symlink_target = kwargs.pop('symlink_target', None)
        if (self.avoid_storage_check or self.symlink_target) and len(self.archive_dirs) != 1:
            raise click.exceptions.UsageError('Invalid number of archive-dirs for --no-storage-access or '
                                              '--symlink-target')
        if bool(self.symlink_target) != bool(self.symlink_backend):
            raise click.exceptions.UsageError('Both or none of --symlink-target and --symlink-backend must be used.')
        super(AttachmentImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--storage-backend', required=True,
                               help="The name of the storage backend used for attachments.")(command)
        command = click.option('--archive-dir', required=True, multiple=True,
                               help="The base path where materials are stored (ArchiveDir in indico.conf). "
                                    "When used multiple times, the dirs are checked in order until a file is "
                                    "found.")(command)
        command = click.option('--default-group-provider', default='legacy-ldap',
                               help="Name of the default group provider")(command)
        command = click.option('--avoid-storage-check', is_flag=True,
                               help="Avoid checking files in storage unless absolutely necessary due to encoding "
                                    "issues. This will migrate all files with size=0.  When this option is specified, "
                                    "--archive-dir must be used exactly once.")(command)
        command = click.option('--symlink-backend',
                               help="The name of the storage backend used for symlinks.")(command)
        command = click.option('--symlink-target',
                               help="If set, any files with a non-UTF8 path will be symlinked in this location and "
                                    "store the path to the symlink instead (relative to the archive dir). "
                                    "When this option is specified, --archive-dir must be used exactly once."
                               )(command)
        return command

    def has_data(self):
        return AttachmentFolder.has_rows or Attachment.has_rows

    def migrate(self):
        self.janitor_user = User.get_one(Config.getInstance().getJanitorUserId())
        with patch_default_group_provider(self.default_group_provider):
            self.migrate_category_attachments()
            self.migrate_event_attachments()
        self.update_merged_ids()

    def update_merged_ids(self):
        self.print_step('updating merged users in attachment acls')
        for p in AttachmentPrincipal.find(User.merged_into_id != None, _join=AttachmentPrincipal.user):  # noqa
            user = p.user
            while p.user.merged_into_user:
                p.user = p.user.merged_into_user
            self.print_success(cformat('%{cyan}{}%{reset} -> %{cyan}{}%{reset}').format(user, p.user), always=True)
        self.print_step('updating merged users in folder acls')
        for p in AttachmentFolderPrincipal.find(User.merged_into_id != None,
                                                _join=AttachmentFolderPrincipal.user):  # noqa
            while p.user.merged_into_user:
                p.user = p.user.merged_into_user
            self.print_success(cformat('%{cyan}{}%{reset} -> %{cyan}{}%{reset}').format(user, p.user), always=True)
        db.session.commit()

    def migrate_category_attachments(self):
        self.print_step('migrating category attachments')

        for category, material, resources in committing_iterator(self._iter_category_materials(), n=1000):
            folder = self._folder_from_material(material, category)
            if not self.quiet:
                self.print_success(cformat('%{cyan}[{}]').format(folder.title),
                                   event_id=category.id)
            for resource in resources:
                attachment = self._attachment_from_resource(folder, material, resource, category)
                if attachment is None:
                    continue
                db.session.add(attachment)
                if not self.quiet:
                    if attachment.type == AttachmentType.link:
                        self.print_success(cformat('- %{cyan}{}').format(attachment.title), event_id=category.id)
                    else:
                        self.print_success(cformat('- %{cyan!}{}').format(attachment.title), event_id=category.id)

    def migrate_event_attachments(self):
        self.print_step('migrating event attachments')

        for event, obj, material, resources in committing_iterator(self._iter_event_materials(), n=1000):
            folder = self._folder_from_material(material, obj)
            db.session.add(LegacyAttachmentFolderMapping(linked_object=obj, material_id=material.id, folder=folder))
            if not self.quiet:
                self.print_success(cformat('%{cyan}[{}]%{reset} %{blue!}({})').format(folder.title, folder.link_repr),
                                   event_id=event.id)
            for resource in resources:
                attachment = self._attachment_from_resource(folder, material, resource, event)
                if attachment is None:
                    continue
                db.session.add(LegacyAttachmentMapping(linked_object=obj, material_id=material.id,
                                                       resource_id=resource.id, attachment=attachment))
                if not self.quiet:
                    if attachment.type == AttachmentType.link:
                        self.print_success(cformat('- %{cyan}{}').format(attachment.title), event_id=event.id)
                    else:
                        self.print_success(cformat('- %{cyan!}{}').format(attachment.title), event_id=event.id)

    def _folder_from_material(self, material, linked_object):
        folder = AttachmentFolder(title=convert_to_unicode(material.title).strip() or 'Material',
                                  description=convert_to_unicode(material.description),
                                  linked_object=linked_object,
                                  is_always_visible=not material._Material__ac._hideFromUnauthorizedUsers)
        protection_from_ac(folder, material._Material__ac)
        db.session.add(folder)
        return folder

    def _get_file_info(self, resource):
        archive_id = resource._LocalFile__archivedId
        repo_path = resource._LocalFile__repository._MaterialLocalRepository__files[archive_id]
        for archive_path in map(bytes, self.archive_dirs):
            path = os.path.join(archive_path, repo_path)
            if any(ord(c) > 127 for c in repo_path):
                foobar = (('strict', 'iso-8859-1'), ('replace', sys.getfilesystemencoding()), ('replace', 'ascii'))
                for mode, enc in foobar:
                    try:
                        dec_path = path.decode('utf-8', mode)
                    except UnicodeDecodeError:
                        dec_path = path.decode('iso-8859-1', mode)
                    enc_path = dec_path.encode(enc, 'replace')
                    if os.path.exists(enc_path):
                        path = enc_path
                        break
                else:
                    parent_path = os.path.dirname(path)
                    candidates = os.listdir(parent_path)
                    if len(candidates) != 1:
                        return None, None, 0
                    path = os.path.join(parent_path, candidates[0])
                    if not os.path.exists(path):
                        return None, None, 0

            assert path
            size = 0 if self.avoid_storage_check else os.path.getsize(path)
            rel_path = os.path.relpath(path, archive_path)
            try:
                rel_path = rel_path.decode('utf-8')
            except UnicodeDecodeError:
                if not self.symlink_target:
                    return None, None, 0
                symlink_name = uuid4()
                symlink = os.path.join(self.symlink_target, bytes(symlink_name))
                os.symlink(path, symlink)
                return self.symlink_backend, symlink_name, size
            else:
                return self.storage_backend, rel_path, size

    def _attachment_from_resource(self, folder, material, resource, base_object=None):
        modified_dt = (getattr(material, '_modificationDS', None) or getattr(base_object, 'startDate', None) or
                       getattr(base_object, '_modificationDS', None) or now_utc())
        data = {'folder': folder,
                'user': self.janitor_user,
                'title': convert_to_unicode(resource.name).strip() or folder.title,
                'description': convert_to_unicode(resource.description)}
        if resource.__class__.__name__ == 'Link':
            data['type'] = AttachmentType.link
            data['link_url'] = resource.url
        else:
            data['type'] = AttachmentType.file
            storage_backend, storage_path, size = self._get_file_info(resource)
            if storage_path is None:
                self.print_error(cformat('%{red!}File {} not found on disk').format(resource._LocalFile__archivedId),
                                 event_id=base_object.id)
                return None
            filename = secure_filename(convert_to_unicode(resource.fileName)) or 'attachment'
            data['file'] = AttachmentFile(user=self.janitor_user, created_dt=modified_dt, filename=filename,
                                          content_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                                          size=size, storage_backend=storage_backend, storage_file_id=storage_path)
        attachment = Attachment(**data)
        protection_from_ac(attachment, resource._Resource__ac)
        db.session.add(attachment)
        # https://bitbucket.org/zzzeek/sqlalchemy/issue/3471/onupdate-runs-for-post_update-updates
        db.session.flush()
        attachment.modified_dt = modified_dt
        return attachment

    def _has_special_protection(self, material, resource):
        material_ac = material._Material__ac
        resource_ac = resource._Resource__ac
        # both inherit
        if resource_ac._accessProtection == 0 and material_ac._accessProtection == 0:
            return False
        # resource is protected
        if resource_ac._accessProtection > 0:
            return True
        # material is protected and resource inherits
        if resource_ac._accessProtection == 0 and material_ac._accessProtection > 0:
            return True
        return False

    def _iter_attachments(self, obj):
        all_materials = chain(obj.materials.itervalues(), [getattr(obj, 'minutes', None)],
                              [getattr(obj, 'slides', None)], [getattr(obj, 'paper', None)],
                              [getattr(obj, 'poster', None)], [getattr(obj, 'video', None)])
        all_materials = (m for m in all_materials if m is not None)
        for material in all_materials:
            # skip minutes with no special protection - they are migrated in the event_notes migration
            resources = [resource for _, resource in material._Material__resources.iteritems() if
                         not (material.id == 'minutes' and resource.id == 'minutes' and
                              not self._has_special_protection(material, resource))]
            if resources:
                yield material, resources

    def _iter_event_materials(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))
        for event in self.flushing_iterator(it):
            for material, resources in self._iter_attachments(event):
                yield event, event, material, resources
            for session in event.sessions.itervalues():
                for material, resources in self._iter_attachments(session):
                    yield event, session, material, resources
            for contrib in event.contributions.itervalues():
                for material, resources in self._iter_attachments(contrib):
                    yield event, contrib, material, resources
                for subcontrib in contrib._subConts:
                    for material, resources in self._iter_attachments(subcontrib):
                        yield event, subcontrib, material, resources

    def _iter_category_materials(self):
        it = self.zodb_root['categories'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['categories']), attrgetter('id'), attrgetter('name'))
        for category in self.flushing_iterator(it):
            for material, resources in self._iter_attachments(category):
                yield category, material, resources
