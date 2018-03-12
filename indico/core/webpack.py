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

from flask import current_app
from flask_webpackext import FlaskWebpackExt
from flask_webpackext.manifest import JinjaManifestLoader
from pywebpack import ManifestLoader

from indico.web.assets.util import get_custom_assets


class IndicoManifestLoader(JinjaManifestLoader):
    def load(self, filepath):
        if current_app.debug or filepath not in JinjaManifestLoader.cache:
            JinjaManifestLoader.cache[filepath] = manifest = ManifestLoader.load(self, filepath)
            self._add_custom_assets(manifest)
        return JinjaManifestLoader.cache[filepath]

    def _add_custom_assets(self, manifest):
        # custom assets (from CUSTOMIZATION_DIR) are not part of the webpack manifest
        # since they are not build with webpack (it's generally not available on the
        # machine running indico), but we add them here anyway so they can be handled
        # without too much extra code, e.g. when building a static site.
        manifest.add(self.entry_cls('__custom.css', get_custom_assets('css')))
        manifest.add(self.entry_cls('__custom.js', get_custom_assets('js')))


webpack = FlaskWebpackExt()
