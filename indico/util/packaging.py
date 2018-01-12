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

import os
import pkgutil
import sys

import pkg_resources


def package_is_editable(package):
    """Check whether the Python package is installed in 'editable' mode"""
    # based on pip.dist_is_editable
    dist = pkg_resources.get_distribution(package)
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.project_name + '.egg-link')
        if os.path.isfile(egg_link):
            return True
    return False


def get_package_root_path(import_name):
    """Get the root path of a package

    Returns ``None`` if the specified import name is invalid or
    points to a module instead of a package.
    """
    loader = pkgutil.get_loader(import_name)
    if loader is None or not loader.is_package(import_name):
        return None
    filepath = loader.get_filename(import_name)
    return os.path.dirname(os.path.abspath(filepath))
