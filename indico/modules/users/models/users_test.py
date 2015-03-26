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

from indico.modules.users import User


def test_can_be_modified():
    user = User()
    # user can modify himself
    assert user.can_be_modified(user)
    # admin can modify anyone
    assert user.can_be_modified(User(is_admin=True))
    # normal users can't
    assert not user.can_be_modified(User())


def test_full_name():
    assert User(first_name='Guinea', last_name='Pig').full_name == 'Guinea Pig'


@pytest.mark.parametrize(('last_name_first', 'last_name_upper', 'abbrev_first_name', 'expected'), (
    (False, False, False, 'Guinea Pig'),
    (False, False, True,  'G. Pig'),
    (False, True,  False, 'Guinea PIG'),
    (False, True,  True,  'G. PIG'),
    (True,  False, False, 'Pig, Guinea'),
    (True,  False, True,  'Pig, G.'),
    (True,  True,  False, 'PIG, Guinea'),
    (True,  True,  True,  'PIG, G.'),
))
def test_get_full_name(last_name_first, last_name_upper, abbrev_first_name, expected):
    user = User(first_name='Guinea', last_name='Pig')
    name = user.get_full_name(last_name_first=last_name_first, last_name_upper=last_name_upper,
                              abbrev_first_name=abbrev_first_name)
    assert name == expected


def test_emails(db):
    user = User(first_name='Guinea', last_name='Pig')
    db.session.add(user)
    db.session.flush()
    assert user.email is None
    assert not user.secondary_emails
    user.email = 'foo@bar.com'
    db.session.flush()
    assert set(user.all_emails) == {'foo@bar.com'}
    user.secondary_emails.append('guinea@pig.com')
    db.session.flush()
    db.session.expire(user)  # all_emails is only updated after expire (or commit)
    assert set(user.all_emails) == {'foo@bar.com', 'guinea@pig.com'}


def test_make_email_primary(db):
    user = User(first_name='Guinea', last_name='Pig', email='guinea@pig.com')
    db.session.add(user)
    db.session.flush()
    with pytest.raises(ValueError):
        user.make_email_primary('tasty@pig.com')
    user.secondary_emails = ['tasty@pig.com', 'little@pig.com']
    db.session.flush()
    user.make_email_primary('tasty@pig.com')
    db.session.expire(user)
    assert user.email == 'tasty@pig.com'
    assert set(user.secondary_emails) == {'guinea@pig.com', 'little@pig.com'}


def test_deletion(db):
    user = User(first_name='Guinea', last_name='Pig', email='foo@bar.com', secondary_emails=['a@b.c'])
    db.session.add(user)
    db.session.flush()
    assert not user.is_deleted
    assert all(not ue.is_user_deleted for ue in user._all_emails)
    user.is_deleted = True
    db.session.flush()
    assert all(ue.is_user_deleted for ue in user._all_emails)


def test_deletion_no_primary_email():
    # this tests setting the is_deleted property on a user with no primary email
    # very unlikely case but let's make sure we never try to set the deleted
    # flag on a None primary email.
    user = User()
    assert user.email is None
    user.is_deleted = True


def test_settings():
    user = User(id=123)
    # make sure it's a bound settings proxy
    assert user.settings._bound_args == (user,)
