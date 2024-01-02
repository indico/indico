# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache."""
    cache.clear()
