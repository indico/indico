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

import errno
import importlib
import os
import re
import sys
from contextlib import contextmanager
from urlparse import urlparse

import click
from ZODB import DB, FileStorage
from ZODB.broken import find_global, Broken
from ZEO.ClientStorage import ClientStorage
from uuid import uuid4

from indico.core.auth import IndicoMultipass, multipass
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.groups import GroupProxy
from indico.modules.groups.legacy import GroupWrapper
from indico.modules.users.legacy import AvatarUserWrapper
from indico.util.console import cformat


class NotBroken(Broken):
    """Like Broken, but it makes the attributes available"""

    def __setstate__(self, state):
        self.__dict__.update(state)


class UnbreakingDB(DB):
    def classFactory(self, connection, modulename, globalname):
        modulename = re.sub(r'^IndexedCatalog\.BTrees\.', 'BTrees.', modulename)
        if globalname == 'PersistentMapping':
            modulename = 'persistent.mapping'
        elif globalname == 'PersistentList':
            modulename = 'persistent.list'
        elif globalname in ('Avatar', 'AvatarUserWrapper'):
            modulename = 'indico_zodbimport.zodb_objects'
            globalname = 'AvatarUserWrapper'
        elif globalname in ('Group', 'LocalGroupWrapper'):
            modulename = 'indico_zodbimport.zodb_objects'
            globalname = 'LocalGroupWrapper'
        elif globalname in ('LDAPGroup', 'LDAPGroupWrapper'):
            modulename = 'indico_zodbimport.zodb_objects'
            globalname = 'LDAPGroupWrapper'
        elif globalname in ('CERNGroup', 'LDAPGroupWrapper'):
            modulename = 'indico_zodbimport.zodb_objects'
            globalname = 'LDAPGroupWrapper'
        return find_global(modulename, globalname, Broken=NotBroken)


def get_storage(zodb_uri):
    uri_parts = urlparse(str(zodb_uri))

    print cformat("%{green}Trying to open {}...").format(zodb_uri)

    if uri_parts.scheme == 'zeo':
        if uri_parts.port is None:
            print cformat("%{yellow}No ZEO port specified. Assuming 9675")

        storage = ClientStorage((uri_parts.hostname, uri_parts.port or 9675),
                                username=uri_parts.username,
                                password=uri_parts.password,
                                realm=uri_parts.path[1:])

    elif uri_parts.scheme in ('file', None):
        storage = FileStorage.FileStorage(uri_parts.path)
    else:
        raise Exception("URI scheme not known: {}".format(uri_parts.scheme))
    print cformat("%{green}Done!")
    return storage


def convert_to_unicode(val, strip=True, _control_char_re=re.compile(ur'[\x00-\x08\x0b-\x0c\x0e-\x1f]')):
    if isinstance(val, str):
        try:
            rv = unicode(val, 'utf-8')
        except UnicodeError:
            rv = unicode(val, 'latin1')
    elif isinstance(val, unicode):
        rv = val
    elif isinstance(val, int):
        rv = unicode(val)
    elif val is None:
        rv = u''
    else:
        raise RuntimeError('Unexpected type {} is found for unicode conversion: {!r}'.format(type(val), val))
    # get rid of hard tabs and control chars
    rv = rv.replace(u'\t', u' ' * 4)
    rv = _control_char_re.sub(u'', rv)
    if strip:
        rv = rv.strip()
    return rv


def convert_principal_list(opt):
    """Converts a 'users' plugin setting to the new format"""
    principals = set()
    for principal in opt._PluginOption__value:
        if principal.__class__.__name__ == 'Avatar':
            principals.add(('Avatar', principal.id))
        else:
            principals.add(('Group', principal.id))
    return list(principals)


def option_value(opt):
    """Gets a plugin option value"""
    value = opt._PluginOption__value
    if isinstance(value, basestring):
        value = convert_to_unicode(value)
    return value


def get_archived_file(f, archive_paths):
    """Returns the name and path of an archived file

    :param f: A `LocalFile` object
    :param archive_paths: The path that was used in the ``ArchiveDir``
                          config option ot a list of multiple paths.
    """
    # this is based pretty much on MaterialLocalRepository.__getFilePath, but we don't
    # call any legacy methods in ZODB migrations to avoid breakage in the future.
    if f is None:
        return None, None
    if isinstance(archive_paths, basestring):
        archive_paths = [archive_paths]
    archive_id = f._LocalFile__archivedId
    repo = f._LocalFile__repository
    for archive_path in archive_paths:
        path = os.path.join(archive_path, repo._MaterialLocalRepository__files[archive_id])
        if os.path.exists(path):
            return f.fileName, path
        for mode, enc in (('strict', 'iso-8859-1'), ('replace', sys.getfilesystemencoding()), ('replace', 'ascii')):
            enc_path = path.decode('utf-8', mode).encode(enc, 'replace')
            if os.path.exists(enc_path):
                return f.fileName, enc_path
    return f.fileName, None


def convert_principal(principal):
    """Converts a legacy principal to PrincipalMixin style"""
    if isinstance(principal, AvatarUserWrapper):
        return principal.user
    elif isinstance(principal, GroupWrapper):
        return principal.group
    elif principal.__class__.__name__ == 'Avatar':
        return AvatarUserWrapper(principal.id).user
    elif principal.__class__.__name__ == 'Group':
        return GroupProxy(principal.id)
    elif principal.__class__.__name__ in {'CERNGroup', 'LDAPGroup', 'NiceGroup'}:
        return GroupProxy(principal.id, multipass.default_group_provider.name)


def protection_from_ac(target, ac, acl_attr='acl', ac_attr='allowed', allow_public=False):
    """Converts AccessController data to ProtectionMixin style

    This needs to run inside the context of `patch_default_group_provider`.

    :param target: The new object that uses ProtectionMixin
    :param ac: The old AccessController
    :param acl_attr: The attribute name for the acl of `target`
    :param ac_attr: The attribute name for the acl in `ac`
    :param allow_public: If the object allows `ProtectionMode.public`.
                         Otherwise, public is converted to inheriting.
    """
    if ac._accessProtection == -1:
        target.protection_mode = ProtectionMode.public if allow_public else ProtectionMode.inheriting
    elif ac._accessProtection == 0:
        target.protection_mode = ProtectionMode.inheriting
    elif ac._accessProtection == 1:
        target.protection_mode = ProtectionMode.protected
        acl = getattr(target, acl_attr)
        for principal in getattr(ac, ac_attr):
            principal = convert_principal(principal)
            assert principal is not None
            acl.add(principal)
    else:
        raise ValueError('Unexpected protection: {}'.format(ac._accessProtection))


@contextmanager
def patch_default_group_provider(provider_name):
    """Monkeypatches Multipass to use a certain default group provider"""
    class FakeProvider(object):
        name = provider_name
    provider = FakeProvider()
    prop = IndicoMultipass.default_group_provider
    IndicoMultipass.default_group_provider = property(lambda m: provider)
    try:
        yield
    finally:
        IndicoMultipass.default_group_provider = prop


class LocalFileImporterMixin(object):
    """This mixin takes care of interpreting arcane LocalFile information,
       handling incorrectly encoded paths and other artifacts.
       Several usage options are added to the CLI (see below).
    """

    def _set_config_options(self, **kwargs):
        self.archive_dirs = kwargs.pop('archive_dir')
        self.avoid_storage_check = kwargs.pop('avoid_storage_check')
        self.symlink_backend = kwargs.pop('symlink_backend')
        self.symlink_target = kwargs.pop('symlink_target', None)
        self.storage_backend = kwargs.pop('storage_backend')

        if (self.avoid_storage_check or self.symlink_target) and len(self.archive_dirs) != 1:
            raise click.exceptions.UsageError('Invalid number of archive-dirs for --no-storage-access or '
                                              '--symlink-target')
        if bool(self.symlink_target) != bool(self.symlink_backend):
            raise click.exceptions.UsageError('Both or none of --symlink-target and --symlink-backend must be used.')
        return kwargs

    @staticmethod
    def decorate_command(command):
        command = click.option('--archive-dir', required=True, multiple=True,
                               help="The base path where materials are stored (ArchiveDir in indico.conf). "
                                    "When used multiple times, the dirs are checked in order until a file is "
                                    "found.")(command)
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
        command = click.option('--storage-backend', required=True,
                               help="The name of the storage backend used for attachments.")(command)
        return command

    def _get_local_file_info(self, resource):
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
                    try:
                        candidates = os.listdir(parent_path)
                    except OSError as e:
                        if e.errno != errno.ENOENT:
                            raise
                        return None, None, 0
                    if len(candidates) != 1:
                        return None, None, 0
                    path = os.path.join(parent_path, candidates[0])
                    if not os.path.exists(path):
                        return None, None, 0

            assert path
            try:
                size = 0 if self.avoid_storage_check else os.path.getsize(path)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
                return None, None, 0
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


def patch_makac():
    """
    For some reason iterating over conferences is abysmally slow
    (3-4 times slower) with the MaKaC package gone so we use a
    custom import hook to make all the `indico.legacy` packages
    importable as `MaKaC`
    """
    class MakacImporter(object):
        def find_module(self, fullname, path=None):
            if fullname.startswith('MaKaC'):
                return self
            return None

        def load_module(self, fullname):
            sys.modules[fullname] = mod = importlib.import_module(fullname.replace('MaKaC', 'indico.legacy'))
            return mod

    sys.meta_path.append(MakacImporter())
