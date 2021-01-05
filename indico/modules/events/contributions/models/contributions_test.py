# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
