# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from hashlib import md5 as _md5

import pytest

from indico.util.passwords import BCryptPassword, PasswordProperty


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
        assert isinstance(salt, str), 'hashpw expects bytes'
        return md5(value)

    bcrypt = mocker.patch('indico.util.passwords.bcrypt')
    bcrypt.gensalt.return_value = 'salt'
    bcrypt.hashpw.side_effect = _hashpw
    bcrypt.checkpw = lambda pwd, pwdhash: md5(pwd) == pwdhash
    return bcrypt


def test_passwordproperty_get_class(mock_bcrypt):
    assert isinstance(Foo.password, PasswordProperty)
    assert Foo.password.backend.hash('test') == '098f6bcd4621d373cade4e832627b4f6'
    assert mock_bcrypt.hashpw.called
    mock_bcrypt.hashpw.assert_called_with(b'test', 'salt')


@pytest.mark.parametrize('password', (u'm\xf6p', 'foo'))
def test_passwordproperty_set(mock_bcrypt, password):
    test = Foo()
    test.password = password
    assert mock_bcrypt.hashpw.called
    mock_bcrypt.hashpw.assert_called_with(password.encode('utf-8'), 'salt')
    assert test._password == md5(password)


@pytest.mark.parametrize('password', ('', None))
@pytest.mark.usefixtures('mock_bcrypt')
def test_passwordproperty_set_invalid(password):
    test = Foo()
    with pytest.raises(ValueError):
        test.password = password


@pytest.mark.usefixtures('mock_bcrypt')
def test_passwordproperty_del():
    test = Foo()
    test.password = 'foo'
    assert test._password == md5('foo')
    del test.password
    assert test._password is None


def test_passwordproperty_get():
    test = Foo()
    assert isinstance(test.password, BCryptPassword)


@pytest.mark.parametrize(('password_hash_unicode', 'password'), (
    (False, 'moep'),
    (True,  'moep'),
    (False, u'm\xf6p'),
    (True,  u'm\xf6p')
))
@pytest.mark.usefixtures('mock_bcrypt')
def test_bcryptpassword_check(password_hash_unicode, password):
    password_hash = bytes(md5(password))
    if password_hash_unicode:
        password_hash = unicode(password_hash)
    pw = BCryptPassword(password_hash)
    assert pw == unicode(password)
    assert pw == unicode(password).encode('utf-8')
    assert pw != u'notthepassword'
    assert pw != 'notthepassword'


@pytest.mark.parametrize(('password_hash', 'password'), (
    (md5(''), ''),
    ('',      ''),
    ('',      'foo'),
    ('foo',   '')
))
@pytest.mark.usefixtures('mock_bcrypt')
def test_bcryptpassword_check_empty(password_hash, password):
    pw = Foo().password
    pw.hash = password_hash
    assert pw != 'xxx'
    assert pw != password
