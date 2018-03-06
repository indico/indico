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
from glob import glob

from indico.core.config import config
from indico.web.flask.util import url_for


def get_asset_path(path, theme=None):
    if theme:
        base = 'theme-{}'.format(theme)
    else:
        base = 'core'
    return os.path.join(base, path)


def _get_custom_files(subdir, pattern):
    customization_dir = config.CUSTOMIZATION_DIR
    if not customization_dir:
        return []
    customization_dir = os.path.join(customization_dir, subdir)
    if not os.path.exists(customization_dir):
        return []
    return sorted(os.path.relpath(x, customization_dir) for x in glob(os.path.join(customization_dir, pattern)))


def get_custom_assets(type_):
    if type_ not in ('js', 'css'):
        raise ValueError('Invalid custom asset type')
    return [url_for('assets.custom', folder=type_, filename=name)
            for name in _get_custom_files(type_, '*.{}'.format(type_))]
