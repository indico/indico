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

import errno
import os

from indico.util.string import unicode_to_ascii, to_unicode
from werkzeug.utils import secure_filename as _secure_filename


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


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
