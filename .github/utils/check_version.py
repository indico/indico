# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import sys
import tomllib
from pathlib import Path

from hatchling.version.core import VersionFile


def _get_pyproject_version(base_dir: Path):
    data = tomllib.loads((base_dir / 'pyproject.toml').read_text())
    # try a static version
    try:
        return data['project']['version']
    except KeyError:
        pass
    # lookup dynamic version
    if 'version' not in data['project'].get('dynamic', ()):
        print('::error::Version is missing and not dynamic')
        sys.exit(1)
    if data['build-system']['build-backend'] != 'hatchling.build':
        print('::error::Dynamic versions are only supported for hatchling build backend')
        sys.exit(1)
    try:
        version_file_path = data['tool']['hatch']['version']['path']
    except KeyError:
        print('::error::Version file path is not defined')
        sys.exit(1)
    version_file_pattern = data['tool']['hatch']['version'].get('pattern', True)
    vf = VersionFile(base_dir, version_file_path)
    return vf.read(pattern=version_file_pattern)


version = _get_pyproject_version(Path('.'))
tag_version = sys.argv[1]

if tag_version != version:
    print(f'::error::Tag version {tag_version} does not match package version {version}')
    sys.exit(1)
