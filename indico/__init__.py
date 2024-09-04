# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.util.mimetypes import register_custom_mimetypes


__version__ = '3.3.4'
PREFERRED_PYTHON_VERSION_SPEC = '~=3.12.2'

register_custom_mimetypes()
