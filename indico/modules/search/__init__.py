# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals


@signals.app_created.connect
def _check_search_provider(app, **kwargs):
    from .base import get_search_provider
    get_search_provider()
