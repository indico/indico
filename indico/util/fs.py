# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import errno
import hashlib
import os
import re
import time
from datetime import datetime

from werkzeug.utils import secure_filename as _secure_filename

from indico.util.string import to_unicode, unicode_to_ascii


_control_char_re = re.compile(r'[\x00-\x1f]+')
_path_seps_re = re.compile(r'[:/\\]+')


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
    filename to plain ASCII for maximum compatibility. It should only
    be used for file system storage, since especially filenames written
    in asian languages likely become useless when stripping anything
    that's not ASCII; use :func:`secure_client_filename` for client-facing
    filenames.

    :param filename: A filename
    :param fallback: The filename to use if there were no safe chars
                     in the original filename.
    """
    if not filename:
        return fallback
    return _secure_filename(unicode_to_ascii(to_unicode(filename))) or fallback


def secure_client_filename(filename, fallback='file'):
    """Return a secure version of filename for clients.

    This removes possibly dangerous characters (which would result in
    unexpected behavior in URLs or archive paths).
    It should never be used to sanitize filenames for server-side storage;
    use :func:`secure_filename` in that case.

    :param filename: A filename
    :param fallback: The filename to use if there are no safe chars
                     after cleaning up the filename.
    """
    if not filename:
        return fallback
    # strip path separators (they may break flask urls not expecting slashes)
    # `:` isn't allowed on windows
    filename = _path_seps_re.sub('_', filename)
    # normalize all kinds of whitespace to a single space
    filename = ' '.join(filename.split())
    # surrounding whitespace is awful
    filename = filename.strip()
    # get rid of control chars
    filename = _control_char_re.sub('', filename)
    # avoid dot-only filenames
    if set(filename) == {'.'}:
        # filenames consisting of 3 or more dots and nothing else would be OK,
        # but still look awfully like special directories, so we just replace
        # any dot-only filename with underscores
        filename = '_' * len(filename)
    # ending dots are invalid on windows and likely break any urlize logic when
    # pasting a link ending in such a filename
    filename = filename.rstrip('.')
    return filename or fallback


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
    # this is not thread safe and in theory prone to a race condition,
    # the indico home dir is usually set to 710 and thus doesn't allow
    # 'others' to access it at all. additionally, the temporary 027
    # umask results in files being created with 640/750 and thus there's
    # no risk of security issues/bugs in case the race condition actually
    # happens (which is extremely unlikely anyawy)
    umask = os.umask(0o027)
    os.umask(umask)
    default = 0o777 if execute else 0o666
    os.chmod(path, default & ~umask)


def get_file_checksum(fileobj, chunk_size=1024*1024, algorithm=hashlib.md5):
    checksum = algorithm()
    while True:
        chunk = fileobj.read(chunk_size)
        if not chunk:
            break
        checksum.update(chunk)
    return unicode(checksum.hexdigest())
