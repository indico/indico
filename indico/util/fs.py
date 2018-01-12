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

import errno
import os
import time
from datetime import datetime

from werkzeug.utils import secure_filename as _secure_filename

from indico.util.string import to_unicode, unicode_to_ascii


def silentremove(filename):
    try:
        os.remove(filename)
        return True
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        return False


def secure_filename(filename, fallback):
    """Returns a secure version of a filename.

    This removes possibly dangerous characters and also converts the
    filename to plain ASCII for maximum compatibility.

    :param filename: A filename
    :param fallback: The filename to use if there were no safe chars
                     in the original filename.
    """
    if not filename:
        return fallback
    return _secure_filename(unicode_to_ascii(to_unicode(filename))) or fallback


def resolve_link(link):
    """Resolve a link to an absolute path.

    :param link: An absolute path to a symlink.
    """
    return os.path.normpath(os.path.join(os.path.dirname(link), os.readlink(link)))


def removedirs(base, name):
    """Delete the leaf dir and try deleting all parents.

    :param base: The base dir `name` is relative to.
    :param name: The path to the directory to be deleted.

    This basically ``rmdir -p`` and acts like :func:`os.removedirs`
    except that it will not ascend above `base`.
    """
    os.rmdir(os.path.join(base, name))
    head, tail = os.path.split(name)
    if not tail:
        head, tail = os.path.split(head)
    while head and tail:
        try:
            os.rmdir(os.path.join(base, head))
        except OSError:
            break
        head, tail = os.path.split(head)


def cleanup_dir(path, min_age, dry_run=False, exclude=None):
    """Delete old files from a directory.

    This recurses into subdirectories and will also delete any empty
    subdirectories.

    :param path: The directory to clean up
    :param min_age: A timedelta specifying how old files need to be
                    so they are deleted.
    :param dry_run: If true, this function will not delete anything
                    but just return the files it would delete.
    :param exclude: A callable that is invoked with the subdirectory
                    (relative to `path`). If it returns ``True``, the
                    directory and all its subdirs will be ignored.
    :return: A set containing the deleted files.
    """
    min_mtime = int(time.mktime((datetime.now() - min_age).timetuple()))
    if not path or path == '/':
        raise ValueError('Invalid path for cleanup: {}'.format(path))
    deleted = set()
    for root, dirs, files in os.walk(path):
        relroot = os.path.relpath(root, path)
        if relroot == '.':
            relroot = ''
        if exclude is not None and exclude(relroot):
            del dirs[:]  # avoid descending into subdirs
            continue
        has_files = False
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.getmtime(filepath) >= min_mtime:
                has_files = True
            elif dry_run or silentremove(filepath):
                deleted.add(os.path.relpath(filepath, path))
            else:
                has_files = True  # deletion failed
        if not dry_run and not has_files and not dirs and relroot:
            removedirs(path, relroot)
    return deleted


def chmod_umask(path, execute=False):
    """Change the permissions of a file to the umask-based default.

    :param path: The path to the file/directory
    :param execute: Whether the x-bit may be set
    """
    # XXX: umask cannot be read except when changing it,
    # so we change it and immediately restore it...
    umask = os.umask(0)
    os.umask(umask)
    default = 0o777 if execute else 0o666
    os.chmod(path, default & ~umask)
