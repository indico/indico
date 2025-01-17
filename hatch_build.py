# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
import os
import subprocess
from pathlib import Path

from babel.messages.pofile import read_po, write_po
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if os.environ.get('READTHEDOCS') == 'True' or version == 'editable':
            return
        _split_all_po_files()
        _compile_languages()
        _compile_languages_react()


def _split_all_po_files():
    translations_dir = Path('indico/translations')
    pot_files = [f for f in translations_dir.glob('*.pot') if f.name != 'messages-all.pot']

    for lc_messages_dir in translations_dir.glob('*/LC_MESSAGES'):
        if lc_messages_dir.parent.name == 'en_US':
            continue

        merged_po_path = lc_messages_dir / 'messages-all.po'

        assert merged_po_path.exists(), f'{merged_po_path} does not exist!'

        for pot_file in pot_files:
            output_po_path = lc_messages_dir / pot_file.name.replace('.pot', '.po')
            _split_po_by_pot(merged_po_path, pot_file, output_po_path)


def _split_po_by_pot(merged_po_path: Path, pot_path: Path, output_po_path: Path):
    with merged_po_path.open('rb') as f:
        merged_catalog = read_po(f)

    with pot_path.open('rb') as f:
        pot_catalog = read_po(f)

    merged_catalog.update(pot_catalog, no_fuzzy_matching=True)
    # For some reason we receive catalogs marked as fuzzy from transifex, and babel skips
    # those by default, even though they are perfectly fine to use...
    merged_catalog.fuzzy = False

    with output_po_path.open('wb') as f:
        write_po(f, merged_catalog, ignore_obsolete=True, width=120)


def _compile_languages():
    from babel.messages.frontend import CompileCatalog
    cmd = CompileCatalog()
    cmd.directory = 'indico/translations'
    cmd.finalize_options()
    cmd.run()


def _compile_languages_react():
    for subdir in Path('indico/translations').iterdir():
        po_file = subdir / 'LC_MESSAGES' / 'messages-react.po'
        json_file = subdir / 'LC_MESSAGES' / 'messages-react.json'
        if not po_file.exists():
            continue
        output = subprocess.check_output(['npx', 'react-jsx-i18n', 'compile', po_file], stderr=subprocess.DEVNULL)
        json.loads(output)  # just to be sure the JSON is valid
        json_file.write_bytes(output)
