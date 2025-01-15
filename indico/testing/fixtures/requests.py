# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from responses import RequestsMock


@pytest.fixture
def mocked_responses():
    with RequestsMock() as rsps:
        yield rsps
