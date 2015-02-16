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

import re
from urlparse import urlparse

from ZODB import DB, FileStorage
from ZODB.broken import find_global, Broken
from ZEO.ClientStorage import ClientStorage

from indico.util.console import colored


class NotBroken(Broken):
    """Like Broken, but it makes the attributes available"""

    def __setstate__(self, state):
        self.__dict__.update(state)


class UnbreakingDB(DB):
    def classFactory(self, connection, modulename, globalname):
        modulename = re.sub(r'^IndexedCatalog\.BTrees\.', 'BTrees.', modulename)
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


def convert_to_unicode(val):
    if isinstance(val, str):
        try:
            return unicode(val, 'utf-8')
        except UnicodeError:
            return unicode(val, 'latin1')
    elif isinstance(val, unicode):
        return val
    elif isinstance(val, int):
        return unicode(val)
    elif val is None:
        return u''
    raise RuntimeError('Unexpected type is found for unicode conversion')


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
