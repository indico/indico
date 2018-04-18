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

from io import BytesIO

import pytest

from indico.core.errors import UserValueError
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.util import (create_personal_data_fields, create_registration,
                                                     import_registrations_from_csv)


@pytest.fixture
def dummy_regform(db, dummy_event):
    regform = RegistrationForm(event=dummy_event, title='Registration Form', currency='USD')
    create_personal_data_fields(regform)

    # enable all fields
    for field in regform.sections[0].fields:
        field.is_enabled = True
    db.session.add(regform)
    db.session.flush()
    return regform


def test_import_registrations(dummy_regform, dummy_user):
    csv = b'\n'.join([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.com',
                      b'Jane,Smith,ACME Inc.,CEO,,jane@example.com',
                      b'Billy Bob,Doe,,,,1337@example.COM'])
    registrations = import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert len(registrations) == 3

    assert registrations[0].full_name == 'John Doe'
    assert registrations[0].user is None
    data = registrations[0].get_personal_data()
    assert data['affiliation'] == 'ACME Inc.'
    assert data['email'] == 'jdoe@example.com'
    assert data['position'] == 'Regional Manager'
    assert data['phone'] == '+1-202-555-0140'

    assert registrations[1].full_name == 'Jane Smith'
    assert registrations[1].user is None
    data = registrations[1].get_personal_data()
    assert data['affiliation'] == 'ACME Inc.'
    assert data['email'] == 'jane@example.com'
    assert data['position'] == 'CEO'
    assert 'phone' not in data

    assert registrations[2].full_name == 'Billy Bob Doe'
    assert registrations[2].user == dummy_user
    data = registrations[2].get_personal_data()
    assert 'affiliation' not in data
    assert data['email'] == '1337@example.com'
    assert 'position' not in data
    assert 'phone' not in data


def test_import_error(dummy_regform):
    create_registration(dummy_regform, {
        'email': 'boss@example.com',
        'first_name': 'Big',
        'last_name': 'Boss'
    }, notify_user=False)

    # missing column
    csv = b'\n'.join([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.com',
                      b'Buggy,Entry,ACME Inc.,CEO,'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'malformed' in e.value.message
    assert 'Row 2' in e.value.message

    # missing e-mail
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.com',
                      b'Buggy,Entry,ACME Inc.,CEO,,'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'missing e-mail' in e.value.message
    assert 'Row 2' in e.value.message

    # bad e-mail
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.com',
                      b'Buggy,Entry,ACME Inc.,CEO,,not-an-email'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'invalid e-mail' in e.value.message
    assert 'Row 2' in e.value.message

    # duplicate e-mail (csv)
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.com',
                      b'Bob,Doe,ACME Inc.,Boss,,bdoe@example.com'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'email address is not unique' in e.value.message
    assert 'Row 2' in e.value.message

    # duplicate e-mail (registration)
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,Supreme Leader,+1-202-555-1337,boss@example.com'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'a registration with this email already exists' in e.value.message
    assert 'Row 1' in e.value.message

    # missing first name
    csv = b'\n'.join([b'Ray,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,rdoe@example.com',
                      b',Buggy,ACME Inc.,CEO,,buggy@example.com'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'missing first' in e.value.message
    assert 'Row 2' in e.value.message
