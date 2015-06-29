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

import os
import re
import sys
from contextlib import contextmanager
from urlparse import urlparse

from ZODB import DB, FileStorage
from ZODB.broken import find_global, Broken
from ZEO.ClientStorage import ClientStorage

from indico.core.auth import IndicoMultipass, multipass
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.groups import GroupProxy
from indico.modules.groups.legacy import GroupWrapper
from indico.modules.users.legacy import AvatarUserWrapper
from indico.util.console import colored


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
        return find_global(modulename, globalname, Broken=NotBroken)


def get_storage(zodb_uri):
    uri_parts = urlparse(str(zodb_uri))

    print colored("Trying to open {}...".format(zodb_uri), 'green')

    if uri_parts.scheme == 'zeo':
        if uri_parts.port is None:
            print colored("No ZEO port specified. Assuming 9675", 'yellow')

        storage = ClientStorage((uri_parts.hostname, uri_parts.port or 9675),
                                username=uri_parts.username,
                                password=uri_parts.password,
                                realm=uri_parts.path[1:])

    elif uri_parts.scheme in ('file', None):
        storage = FileStorage.FileStorage(uri_parts.path)
    else:
        raise Exception("URI scheme not known: {}".format(uri_parts.scheme))
    print colored("Done!", 'green')
    return storage


def convert_to_unicode(val, _control_char_re=re.compile(ur'[\x00-\x08\x0b-\x0c\x0e-\x1f]')):
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
            if isinstance(principal, AvatarUserWrapper):
                principal = principal.user
            elif isinstance(principal, GroupWrapper):
                principal = principal.group
            elif principal.__class__.__name__ == 'Avatar':
                principal = AvatarUserWrapper(principal.id).user
            elif principal.__class__.__name__ == 'Group':
                principal = GroupProxy(principal.id)
            elif principal.__class__.__name__ in {'CERNGroup', 'LDAPGroup', 'NiceGroup'}:
                principal = GroupProxy(principal.id, multipass.default_group_provider.name)
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
