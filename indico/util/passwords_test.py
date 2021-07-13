# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import hashlib

import pytest

from indico.core import signals
from indico.util.passwords import BCryptPassword, PasswordProperty, SHA256Token, validate_secure_password


def md5(s):
    if isinstance(s, str):
        s = s.encode()
    return hashlib.md5(s).hexdigest()


def sha256(s):
    if isinstance(s, str):
        s = s.encode()
    return hashlib.sha256(s).hexdigest()


class Foo:
    def __init__(self, password=None):
        if password is not None:
            self.password = password

    password = PasswordProperty('_password')


@pytest.fixture
def mock_bcrypt(mocker):
    def _hashpw(value, salt):
        assert isinstance(value, bytes), 'hashpw expects bytes'
        assert isinstance(salt, bytes), 'hashpw expects bytes'
        return md5(value).encode()

    bcrypt = mocker.patch('indico.util.passwords.bcrypt')
    bcrypt.gensalt.return_value = b'salt'
    bcrypt.hashpw.side_effect = _hashpw
    bcrypt.checkpw = lambda pwd, pwdhash: md5(pwd).encode() == pwdhash
    return bcrypt


def test_passwordproperty_get_class(mock_bcrypt):
    assert isinstance(Foo.password, PasswordProperty)
    assert Foo.password.backend.create_hash('test') == '098f6bcd4621d373cade4e832627b4f6'
    assert mock_bcrypt.hashpw.called
    mock_bcrypt.hashpw.assert_called_with(b'test', b'salt')


@pytest.mark.parametrize('password', ('möp', 'foo'))
def test_passwordproperty_set(mock_bcrypt, password):
    test = Foo()
    test.password = password
    assert mock_bcrypt.hashpw.called
    mock_bcrypt.hashpw.assert_called_with(password.encode(), b'salt')
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


@pytest.mark.parametrize('password', ('moep', 'möp'))
@pytest.mark.usefixtures('mock_bcrypt')
def test_bcryptpassword_check(password):
    password_hash = md5(password)
    pw = BCryptPassword(password_hash)
    assert pw == password
    assert pw != 'notthepassword'


@pytest.mark.parametrize('password', ('moep', 'möp'))
def test_sha256token_check(password):
    password_hash = sha256(password)
    pw = SHA256Token(password_hash)
    assert pw == password
    assert pw != 'notthepassword'


@pytest.mark.usefixtures('mock_bcrypt')
def test_bcryptpassword_fail_bytes():
    pw = BCryptPassword(md5('foo'))
    with pytest.raises(TypeError) as exc_info:
        pw == b'foo'
    assert str(exc_info.value) == "password must be str, not <class 'bytes'>"


@pytest.mark.parametrize(('password_hash', 'password'), (
    (md5(b''), ''),
    ('', ''),
    ('', 'foo'),
    ('foo', '')
))
@pytest.mark.usefixtures('mock_bcrypt')
def test_bcryptpassword_check_empty(password_hash, password):
    pw = Foo().password
    pw.hash = password_hash
    assert pw != 'xxx'
    assert pw != password


@pytest.mark.parametrize(('password', 'username', 'expected'), (
    ('this is a long password', '', None),
    ('this is a long password', 'long', None),
    ('this is long', 'this is', 'your username'),
    ('correct horse battery staple', '', 'previous data breaches'),
    ('badsignal', '', 'signalfail'),
    ('short', '', '8 characters'),
    ('pw for indico', '', 'word "indico"'),
    ('INDICO password', '', 'word "indico"'),
    ('1nd1c0 password', '', 'word "indico"'),
))
def test_validate_secure_password(monkeypatch, password, username, expected):
    signal_called = False

    def _mock_pwned(password, fast=False):
        return password == 'correct horse battery staple'

    def _signal_fn(sender, **kw):
        nonlocal signal_called
        signal_called = True
        assert sender == 'test'
        assert username == kw['username']
        if kw['password'] == 'badsignal':
            return 'signalfail'

    monkeypatch.setattr('indico.util.passwords.check_password_pwned', _mock_pwned)
    with signals.core.check_password_secure.connected_to(_signal_fn):
        rv = validate_secure_password('test', password, username=username)
    assert signal_called
    if expected is None:
        assert rv is None
    else:
        assert expected in rv
