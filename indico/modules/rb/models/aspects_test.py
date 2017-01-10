# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.modules.rb.models.aspects import Aspect


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_default_on_startup(dummy_location, db):
    aspect = Aspect(name=u'Test', center_latitude='', center_longitude='', zoom_level=0, top_left_latitude=0,
                    top_left_longitude=0, bottom_right_latitude=0, bottom_right_longitude=0)
    dummy_location.aspects.append(aspect)
    db.session.flush()
    assert not aspect.default_on_startup
    dummy_location.default_aspect = aspect
    db.session.flush()
    assert aspect.default_on_startup
