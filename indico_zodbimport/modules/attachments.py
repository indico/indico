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
from collections import OrderedDict
from itertools import chain
from operator import attrgetter
from uuid import uuid4

import click

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.attachments.models.attachments import Attachment, AttachmentType, AttachmentFile
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.models.legacy_mapping import LegacyAttachmentFolderMapping, LegacyAttachmentMapping
from indico.modules.attachments.models.principals import AttachmentPrincipal, AttachmentFolderPrincipal
from indico.modules.users import User
from indico.util.console import cformat, verbose_iterator
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import protection_from_ac, patch_default_group_provider


def _link_repr(folder):
    _all_columns = {'category_id', 'event_id', 'contribution_id', 'subcontribution_id', 'session_id'}
    info = [('link_type', folder['link_type'].name if folder['link_type'] is not None else 'None')]
    info.extend((key, folder[key]) for key in _all_columns if folder[key] is not None)
    return ', '.join('{}={}'.format(key, value) for key, value in info)


def _get_pg_id(col):
    table = col.class_.__table__.fullname
    return db.session.query(db.func.nextval(db.func.pg_get_serial_sequence(table, col.name))).one()[0]


def _sa_to_dict(obj):
    return {k: v for k, v in obj.__dict__.iteritems() if k[0] != '_'}


class ProtectionTarget(object):
    def __init__(self):
        self.acl = set()
        self.protection_mode = None

    def _make_principal(self, principal, **data):
        if principal.is_group:
            if principal.is_local:
                data['type'] = PrincipalType.local_group
                data['local_group_id'] = principal.group.id
            else:
                data['type'] = PrincipalType.multipass_group
                data['multipass_group_provider'] = principal.provider
                data['multipass_group_name'] = principal.name
        else:
            data['type'] = PrincipalType.user
            data['user_id'] = principal.id
        return data

    def make_principal_rows(self, **data):
        return [self._make_principal(principal, **data) for principal in self.acl]


class AttachmentImporter(Importer):
    def __init__(self, **kwargs):
        self.janitor_user_id = kwargs.pop('janitor_user_id')
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
        command = click.option('--janitor-user-id', type=int, required=True, help="The ID of the Janitor user")(command)
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
        # disable onupdate for attachment lastmod timestamp
        # see https://bitbucket.org/zzzeek/sqlalchemy/issue/3471/ why it's needed
        Attachment.__table__.columns.modified_dt.onupdate = None
        janitor_user = User.get_one(self.janitor_user_id)
        self.print_msg('Using janitor user {}'.format(janitor_user), always=True)
        self.janitor_user_id = janitor_user.id
        self.todo = OrderedDict([
            (AttachmentFolder, []),
            (AttachmentFolderPrincipal, []),
            (Attachment, []),
            (AttachmentPrincipal, []),
            (AttachmentFile, []),
            (LegacyAttachmentFolderMapping, []),
            (LegacyAttachmentMapping, [])
        ])
        self.ids = {
            AttachmentFolder: _get_pg_id(AttachmentFolder.id),
            Attachment: _get_pg_id(Attachment.id),
            AttachmentFile: _get_pg_id(AttachmentFile.id),
        }
        with patch_default_group_provider(self.default_group_provider):
            self.migrate_category_attachments()
            self.migrate_event_attachments()

        self.fix_attachment_file_ids()
        self.print_step('fixing id sequences')
        self.fix_sequences('attachments')
        self.update_merged_ids()

    def _get_id(self, mapper):
        id_ = self.ids[mapper]
        self.ids[mapper] += 1
        return id_

    def process_todo(self):
        for mapper, mappings in self.todo.iteritems():
            db.session.bulk_insert_mappings(mapper, mappings)
            del mappings[:]
        db.session.commit()

    def _committing_iterator(self, iterable):
        for i, data in enumerate(iterable, 1):
            yield data
            if i % 10000 == 0:
                self.process_todo()
                db.session.commit()
        self.process_todo()
        db.session.commit()

    def fix_attachment_file_ids(self):
        db.session.execute('UPDATE attachments.attachments a SET file_id = (SELECT id FROM attachments.files WHERE '
                           'attachment_id = a.id) WHERE type = 1')


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

        for category, material, resources in self._committing_iterator(self._iter_category_materials()):
            folder = self._folder_from_material(material, category)
            if not self.quiet:
                self.print_success(cformat('%{cyan}[{}]').format(folder['title']), event_id=category.id)
            for resource in resources:
                attachment = self._attachment_from_resource(folder, material, resource, category)
                if attachment is None:
                    continue
                if not self.quiet:
                    if attachment['type'] == AttachmentType.link:
                        self.print_success(cformat('- %{cyan}{}').format(attachment['title']), event_id=category.id)
                    else:
                        self.print_success(cformat('- %{cyan!}{}').format(attachment['title']), event_id=category.id)

    def migrate_event_attachments(self):
        self.print_step('migrating event attachments')

        for event, obj, material, resources in self._committing_iterator(self._iter_event_materials()):
            folder = self._folder_from_material(material, obj)
            lm = LegacyAttachmentFolderMapping(linked_object=obj, material_id=material.id, folder_id=folder['id'])
            self.todo[LegacyAttachmentFolderMapping].append(_sa_to_dict(lm))
            if not self.quiet:
                self.print_success(cformat('%{cyan}[{}]%{reset} %{blue!}({})').format(folder['title'],
                                                                                      _link_repr(folder)),
                                   event_id=event.id)
            for resource in resources:
                attachment = self._attachment_from_resource(folder, material, resource, event)
                if attachment is None:
                    continue
                lm = LegacyAttachmentMapping(linked_object=obj, material_id=material.id, resource_id=resource.id,
                                             attachment_id=attachment['id'])
                self.todo[LegacyAttachmentMapping].append(_sa_to_dict(lm))
                if not self.quiet:
                    if attachment['type'] == AttachmentType.link:
                        self.print_success(cformat('- %{cyan}{}').format(attachment['title']), event_id=event.id)
                    else:
                        self.print_success(cformat('- %{cyan!}{}').format(attachment['title']), event_id=event.id)

    def _folder_from_material(self, material, linked_object):
        folder_obj = AttachmentFolder(id=self._get_id(AttachmentFolder),
                                      title=convert_to_unicode(material.title).strip() or 'Material',
                                      description=convert_to_unicode(material.description),
                                      linked_object=linked_object,
                                      is_always_visible=not getattr(material._Material__ac,
                                                                    '_hideFromUnauthorizedUsers', False))
        folder = _sa_to_dict(folder_obj)
        self.todo[AttachmentFolder].append(folder)
        tmp = ProtectionTarget()
        protection_from_ac(tmp, material._Material__ac)
        self.todo[AttachmentFolderPrincipal] += tmp.make_principal_rows(folder_id=folder['id'])
        folder['protection_mode'] = tmp.protection_mode
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
        data = {'id': self._get_id(Attachment),
                'folder_id': folder['id'],
                'user_id': self.janitor_user_id,
                'title': convert_to_unicode(resource.name).strip() or folder['title'],
                'description': convert_to_unicode(resource.description),
                'modified_dt': modified_dt}
        if resource.__class__.__name__ == 'Link':
            data['type'] = AttachmentType.link
            data['link_url'] = convert_to_unicode(resource.url).strip()
            if not data['link_url']:
                self.print_error(cformat('%{red!}[{}] Skipping link, missing URL').format(data['title']),
                                 event_id=base_object.id)
                return None
        else:
            data['type'] = AttachmentType.file
            storage_backend, storage_path, size = self._get_file_info(resource)
            if storage_path is None:
                self.print_error(cformat('%{red!}File {} not found on disk').format(resource._LocalFile__archivedId),
                                 event_id=base_object.id)
                return None
            filename = secure_filename(convert_to_unicode(resource.fileName), 'attachment')
            file_data = {'id': self._get_id(AttachmentFile),
                         'attachment_id': data['id'],
                         'user_id': self.janitor_user_id,
                         'created_dt': modified_dt,
                         'filename': filename,
                         'content_type': mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                         'size': size,
                         'storage_backend': storage_backend,
                         'storage_file_id': storage_path}
            self.todo[AttachmentFile].append(file_data)
        tmp = ProtectionTarget()
        protection_from_ac(tmp, resource._Resource__ac)
        self.todo[AttachmentPrincipal] += tmp.make_principal_rows(attachment_id=data['id'])
        data['protection_mode'] = tmp.protection_mode
        self.todo[Attachment].append(data)
        return data

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
