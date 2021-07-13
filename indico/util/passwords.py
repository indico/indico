# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import functools
import hashlib
import re

import bcrypt
import requests

from indico.util.i18n import _


class BCryptPassword:
    def __init__(self, pwhash):
        if pwhash is not None and not isinstance(pwhash, str):
            raise TypeError(f'pwhash must be str or None, not {type(pwhash)}')
        self.hash = pwhash

    def __eq__(self, value):
        if not self.hash or not value:
            # For security reasons we never consider an empty password/hash valid
            return False
        if not isinstance(value, str):
            raise TypeError(f'password must be str, not {type(value)}')
        return bcrypt.checkpw(value.encode(), self.hash.encode())

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):  # pragma: no cover
        return hash(self.hash)

    def __repr__(self):
        return f'<BCryptPassword({self.hash})>'

    @staticmethod
    def create_hash(value):
        return bcrypt.hashpw(value.encode(), bcrypt.gensalt()).decode()


class SHA256Token:
    def __init__(self, pwhash):
        if pwhash is not None and not isinstance(pwhash, str):
            raise TypeError(f'pwhash must be str or None, not {type(pwhash)}')
        self.hash = pwhash

    def __eq__(self, value):
        if not self.hash or not value:
            # For security reasons we never consider an empty password/hash valid
            return False
        if not isinstance(value, str):
            raise TypeError(f'password must be str, not {type(value)}')
        return hashlib.sha256(value.encode()).hexdigest() == self.hash

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):  # pragma: no cover
        return hash(self.hash)

    def __repr__(self):
        return f'<SHA256Token({self.hash})>'

    def __str__(self):
        raise RuntimeError('Hashed tokens have no string representation')

    @staticmethod
    def create_hash(value):
        return hashlib.sha256(value.encode()).hexdigest()


class PasswordProperty:
    """Define a hashed password property.

    When reading this property, it will return an object which will
    let you use the ``==`` operator to compare  the password against
    a plaintext password.  When assigning a value to it, it will be
    hashed and stored in :attr:`attr` of the containing object.

    :param attr: The attribute of the containing object where the
                 password hash is stored.
    :param backend: The password backend that handles hashing/checking
                    passwords.
    """

    def __init__(self, attr, backend=BCryptPassword):
        self.attr = attr
        self.backend = backend

    def __get__(self, instance, owner):
        return self.backend(getattr(instance, self.attr, None)) if instance is not None else self

    def __set__(self, instance, value):
        if not value:
            raise ValueError('Password may not be empty')
        setattr(instance, self.attr, self.backend.create_hash(value))

    def __delete__(self, instance):
        setattr(instance, self.attr, None)


class TokenProperty(PasswordProperty):
    """Similar to `PasswordProperty` but tailored towards API tokens.

    Since tokens are used much more often than passwords, they use
    a fast hash algorithm instead of a secure one. This is not a
    problem for tokens as they are fully random and much longer
    than the typical password or even passphrase.
    """

    def __init__(self, attr):
        super().__init__(attr, backend=SHA256Token)

    def __set__(self, instance, value):
        if len(value) < 30:
            raise ValueError('Token is too short')
        super().__set__(instance, value)


@functools.lru_cache
def _get_pwned_hashes(prefix, timeout=1):
    try:
        resp = requests.get(f'https://api.pwnedpasswords.com/range/{prefix}', timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    return {x.split(':', 1)[0] for x in resp.text.splitlines() if not x.endswith(':0')}


def check_password_pwned(password, fast=False):
    """Check if a password is in the pwned-passwords list.

    :param password: The plaintext password
    :param fast: Whether the check should finish quickly, even if that may
                 indicate not being able to check the password. This should
                 be used during interactive requests
    :return: A bool indicating whether the password has been pwned or not,
             or `None` in case checking it was not possible.
    """
    timeout = 1 if fast else 3
    sha = hashlib.sha1(password.encode()).hexdigest().upper()
    hashes = _get_pwned_hashes(sha[:5], timeout)
    if hashes is None:
        return None
    return sha[5:] in hashes


def validate_secure_password(context, password, *, username='', fast=False):
    """Check if a password is considered secure.

    A password is considered secure if it:

    - is at least 8 characters long
    - does not contain the username unless the username is <5 chars and the password is >16 chars long
    - does not contain the strings 'indico' (or common variations)
    - is not in the pwned password list

    :param context: A string indicating the context where the password is used
    :param password: The plaintext password
    :param username: The corresponding username (may be empty if not applicable)
    :param fast: Whether the check should finish quickly, even if that may
                 indicate not being able to check the password against the list
                 of pwned passwords. This should be used during interactive requests
                 where slowdowns are generally frowned upon (e.g. during login).
    :return: A string indicating why the password is bad, or `None if it's secure.
    """
    from indico.core import signals
    from indico.util.signals import values_from_signal

    # See https://pages.nist.gov/800-63-3/sp800-63b.html#-511-memorized-secrets for some useful
    # guidelines for passwords. Ideally we would also perform a dictionary check, but unless we
    # rely on someone installing OS packages with dictionaries we don't have one available, and
    # there's a good chance that single dictionary words are already included in the pwned password
    # list.

    if errors := values_from_signal(signals.core.check_password_secure.send(context, username=username,
                                                                            password=password),
                                    as_list=True):
        return errors[0]

    if len(password) < 8:
        return _('Passwords must be at least 8 characters long.')

    if re.search(r'[i1|]nd[1i|]c[o0]', password.lower()):
        return _('Passwords may not contain the word "indico" or variations.')

    if len(username) >= 5 and len(password) <= 16 and username.lower() in password.lower():
        return _('Passwords may not contain your username.')

    if check_password_pwned(password):
        return _('This password has been seen in previous data breaches.')
