# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os

from flask_webpackext import FlaskWebpackExt
from flask_webpackext.manifest import JinjaManifestLoader
from pywebpack import ManifestLoader

from indico.web.assets.util import get_custom_assets


class IndicoManifestLoader(JinjaManifestLoader):
    cache = {}

    def __init__(self, *args, **kwargs):
        self.custom = kwargs.pop('custom', True)
        super(IndicoManifestLoader, self).__init__(*args, **kwargs)

    def load(self, filepath):
        key = (filepath, os.path.getmtime(filepath))
        if key not in IndicoManifestLoader.cache:
            IndicoManifestLoader.cache[key] = manifest = ManifestLoader.load(self, filepath)
            if self.custom:
                self._add_custom_assets(manifest)
        return IndicoManifestLoader.cache[key]

    def _add_custom_assets(self, manifest):
        # custom assets (from CUSTOMIZATION_DIR) are not part of the webpack manifest
        # since they are not build with webpack (it's generally not available on the
        # machine running indico), but we add them here anyway so they can be handled
        # without too much extra code, e.g. when building a static site.
        manifest.add(self.entry_cls('__custom.css', get_custom_assets('css')))
        manifest.add(self.entry_cls('__custom.js', get_custom_assets('js')))


webpack = FlaskWebpackExt()
