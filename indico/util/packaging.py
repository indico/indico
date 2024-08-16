# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import sys
from importlib.metadata import distribution
from importlib.util import find_spec
from pathlib import Path


def package_is_editable(package):
    """Check whether the Python package is installed in 'editable' mode."""
    # based on pip.dist_is_editable
    dist = distribution(package)
    for path_item in sys.path:
        if (Path(path_item) / f'{dist.name}.egg-link').is_file():  # setuptools legacy
            return True
        if any(Path(path_item).glob(f'__editable__.{dist.name}-*.pth')):  # setuptools new
            return True
        if (Path(path_item) / f'_{dist.name}.pth').is_file():  # hatchling
            return True
    return False


def get_package_root_path(import_name):
    """Get the root path of a package.

    Returns ``None`` if the specified import name is invalid or
    points to a module instead of a package.
    """
    spec = find_spec(import_name)
    if spec is None or not spec.parent:
        # no parent if it's not a package (PEP 451)
        return None
    paths = spec.submodule_search_locations
    assert len(paths) == 1
    return paths[0]
