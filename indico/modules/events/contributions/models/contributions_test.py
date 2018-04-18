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

from __future__ import unicode_literals

from datetime import timedelta

from flask import g

import indico.modules.events.contributions.models.contributions as contrib_module
from indico.modules.events.contributions.models.contributions import Contribution


class Incrementer(object):
    def __init__(self):
        self.counter = 0

    def __call__(self, _col, _filter, n=1):
        self.counter += n
        return self.counter

    def __eq__(self, n):
        return self.counter == n


def test_contrib_friendly_id(monkeypatch, dummy_event, create_contribution):
    counter = Incrementer()
    monkeypatch.setattr(contrib_module, 'increment_and_get', counter)

    contrib_1 = create_contribution(dummy_event, 'Contribution 1', timedelta(minutes=60))
    assert contrib_1.friendly_id == 1

    contrib_2 = create_contribution(dummy_event, 'Contribution 2', timedelta(minutes=60))
    assert contrib_2.friendly_id == 2

    assert counter == 2

    # pre-allocate 8 friendly ids
    Contribution.allocate_friendly_ids(dummy_event, 8)
    assert g.friendly_ids[Contribution][dummy_event.id] == range(3, 11)
    assert counter == 10

    for fid in g.friendly_ids[Contribution][dummy_event.id][:]:
        contrib = create_contribution(dummy_event, 'Contribution {}'.format(fid), timedelta(minutes=30))
        assert contrib.friendly_id == fid

    # increment_and_get doesn't get called because the ids
    # have been pre-allocated
    assert counter == 10
