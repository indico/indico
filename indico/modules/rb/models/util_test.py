# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime, time, timedelta

import pytest

from indico.modules.rb.models.reservation_occurrences import ReservationOccurrenceState
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.testing.util import bool_matrix


pytest_plugins = 'indico.modules.rb.testing.fixtures'


@pytest.mark.parametrize(
    ('not_repeating', 'only_one_valid', 'propagate', 'proxied'),
    bool_matrix('..0', expect=False) +
    bool_matrix('..1', expect='any_dynamic')
)
@pytest.mark.usefixtures('smtp')
def test_proxy_to_reservation_if_last_valid_occurrence(db, mocker, create_reservation, dummy_user,
                                                       not_repeating, only_one_valid, propagate, proxied, freeze_time):
    resv = create_reservation(start_dt=datetime.combine(date.today(), time(8)),
                              end_dt=datetime.combine(date.today() + timedelta(days=1), time(17)),
                              repeat_frequency=RepeatFrequency.NEVER if not_repeating else RepeatFrequency.DAY)
    freeze_time(datetime.combine(date.today(), time(8)))
    if only_one_valid:
        for occ in resv.occurrences[1:]:
            occ.state = ReservationOccurrenceState.cancelled
        db.session.flush()

    occ = resv.occurrences.first()
    mocker.patch.object(resv, 'cancel')
    occ.cancel(user=dummy_user, propagate=propagate)
    assert resv.cancel.called == proxied
