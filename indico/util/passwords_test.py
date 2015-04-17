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

from hashlib import md5 as _md5

import pytest

from indico.util.passwords import PasswordProperty, BCryptPassword


def md5(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return _md5(s).hexdigest()


class Foo(object):
    def __init__(self, password=None):
        if password is not None:
            self.password = password

    password = PasswordProperty('_password')


@pytest.fixture
def mock_bcrypt(mocker):
    def _hashpw(value, salt):
        assert isinstance(value, str), 'hashpw expects bytes'
        return md5(value)

    bcrypt = mocker.patch('indico.util.passwords.bcrypt')
    bcrypt.gensalt.return_value = 'salt'
    bcrypt.hashpw.side_effect = _hashpw
    return bcrypt


@pytest.mark.parametrize('password', (u'm\xf6p', 'foo'))
def test_passwordproperty_set(mock_bcrypt, password):
    test = Foo()
    test.password = password
    assert mock_bcrypt.hashpw.called
    mock_bcrypt.hashpw.assert_called_with(password.encode('utf-8'), 'salt')
    assert test._password == md5(password)


@pytest.mark.parametrize('password', ('', None))
def test_passwordproperty_set_invalid(mock_bcrypt, password):
    test = Foo()
    with pytest.raises(ValueError):
        test.password = password


def test_passwordproperty_del(mock_bcrypt):
    test = Foo()
    test.password = 'foo'
    assert test._password == md5('foo')
    del test.password
    assert test._password is None


def test_passwordproperty_get(mock_bcrypt):
    test = Foo()
    test.password = 'foo'
    assert isinstance(test.password, BCryptPassword)
    assert test.password == 'foo'
    assert test.password == u'foo'
    assert test.password != 'bar'
    assert test.password != u'bar'


def test_bcryptpassword_eq(mock_bcrypt):
    test = Foo()
    test.password = 'foo'
    pw = test.password
    pw.hash = ''
    assert pw != 'foo'
    assert pw != ''
