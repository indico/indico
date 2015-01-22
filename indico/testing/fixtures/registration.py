# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import pytest
from mock import MagicMock


@pytest.fixture
def create_registrant(dummy_event):
    """Returns a callable which lets you create a registrant for an event"""

    def _create_registrant(event=dummy_event, id_=0, **params):
        registrant = MagicMock(id=id_)
        registrant.getId.return_value = registrant.id
        registrant.getConference.return_value = dummy_event
        return registrant

    return _create_registrant


@pytest.fixture
def dummy_registrant(create_registrant):
    return create_registrant()
