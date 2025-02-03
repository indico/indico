# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.users.models.affiliations import Affiliation


@pytest.mark.parametrize('none_field', ('street', 'postcode', 'city', 'country_code'))
def test_get_or_create_from_data_none_empty_string(db, none_field):
    data = {
        'name': 'Atlantis Institute of Fake Science',
        'street': 'Somewhere',
        'postcode': '31337 Deep Below',
        'city': 'nowhere',
        'country_code': 'XX',
    }
    data[none_field] = None

    # create initial one
    assert not Affiliation.query.has_rows()
    db.session.add(Affiliation.get_or_create_from_data(data))
    assert Affiliation.query.count() == 1
    # make sure we don't recreate it (DB has empty string, data has None)
    db.session.add(Affiliation.get_or_create_from_data(data))
    assert Affiliation.query.count() == 1
    # make sure we also don't recreate it with data having an empty string
    data[none_field] = ''
    db.session.add(Affiliation.get_or_create_from_data(data))
    assert Affiliation.query.count() == 1
