# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import warnings

from indico.util.mimetypes import register_custom_mimetypes


__version__ = '2.3.3'

register_custom_mimetypes()

# TODO: remove in 3.0
warnings.filterwarnings('ignore', message='Python 2 is no longer supported by the Python core team.',
                        module='authlib')
warnings.filterwarnings('ignore', message='Python 2 is no longer supported by the Python core team.',
                        module='cryptography')
