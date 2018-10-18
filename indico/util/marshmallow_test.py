# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import absolute_import, unicode_literals

from datetime import datetime

import pytest
import pytz
from marshmallow import ValidationError

from indico.util.marshmallow import NaiveDateTime


def test_NaiveDateTime_serialize():
    now = datetime.now()
    utc_now = pytz.utc.localize(datetime.utcnow())
    obj = type(b'Test', (object,), {
        b'naive': now,
        b'aware': utc_now,
    })
    field = NaiveDateTime()
    assert field.serialize('naive', obj) == now.isoformat()
    with pytest.raises(AssertionError):
        field.serialize('aware', obj)


def test_NaiveDateTime_deserialize():
    now = datetime.now()
    utc_now = pytz.utc.localize(datetime.utcnow())
    field = NaiveDateTime()
    assert field.deserialize(now.isoformat()) == now
    with pytest.raises(ValidationError):
        field.deserialize(utc_now.isoformat())
