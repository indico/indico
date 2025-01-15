# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import sys
from importlib.util import find_spec

from setuptools.config.expand import StaticModule


package = 'indico'
sys.path.insert(0, os.getcwd())
version = StaticModule(package, find_spec(package)).__version__
tag_version = sys.argv[1]

if tag_version != version:
    print(f'::error::Tag version {tag_version} does not match package version {version}')
    sys.exit(1)
