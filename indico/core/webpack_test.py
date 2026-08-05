# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from pywebpack import Manifest, ManifestEntry, ManifestLoader

from indico.core.webpack import IndicoManifestLoader


def test_load_does_not_cache_incomplete_custom_manifest(tmp_path, mocker):
    manifest_path = tmp_path / 'manifest.json'
    manifest_path.touch()  # needed for the mtime cache key
    mocker.patch.object(IndicoManifestLoader, 'cache', {})
    mocker.patch.object(ManifestLoader, 'load', side_effect=lambda *args: Manifest())

    js_load_started = Event()
    continue_js_load = Event()

    def get_custom_assets(asset_type):
        if asset_type == 'js' and not js_load_started.is_set():
            js_load_started.set()
            assert continue_js_load.wait(timeout=5)
        return [f'custom.{asset_type}']

    mocker.patch('indico.core.webpack.get_custom_assets', side_effect=get_custom_assets)
    loader = IndicoManifestLoader(manifest_cls=Manifest, entry_cls=ManifestEntry)

    def load_and_check_custom_assets():
        manifest = loader.load(manifest_path)
        entry_names = {entry.name for entry in manifest}
        return {'__custom.css', '__custom.js'} <= entry_names

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_load = executor.submit(loader.load, manifest_path)
        assert js_load_started.wait(timeout=5)
        second_load = executor.submit(load_and_check_custom_assets)
        try:
            second_has_custom_assets = second_load.result(timeout=5)
        finally:
            continue_js_load.set()
        first_load.result(timeout=5)

    assert second_has_custom_assets
