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

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if os.environ.get('READTHEDOCS') == 'True' or version == 'editable':
            return
        _compile_languages()
        _compile_languages_react()


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
