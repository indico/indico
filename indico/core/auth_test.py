# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from limits import parse_many

from indico.core.auth import (get_exceeded_login_rate_limiter, get_exceeded_signup_rate_limiter, login_rate_limiter,
                              login_rate_limiter_user, signup_rate_limiter, signup_rate_limiter_email)


def test_get_exceeded_login_rate_limiter_returns_global():
    login_rate_limiter.limits = parse_many('1 per 1 minute')
    login_rate_limiter_user.limits = []
    # Test that the global limiter is not exceeded
    assert get_exceeded_login_rate_limiter() is None
    # Test that the global limiter is exceeded
    login_rate_limiter.hit()
    assert get_exceeded_login_rate_limiter() == login_rate_limiter


def test_get_exceeded_login_rate_limiter_returns_scoped():
    identifier = 'foo'
    login_rate_limiter.limits = parse_many('1 per 1 minute')
    login_rate_limiter_user.limits = parse_many('1 per 1 minute')
    # Test that the global limiter is still active if not checking for a user
    login_rate_limiter.hit()
    assert get_exceeded_login_rate_limiter() == login_rate_limiter
    # Test that limiter is not exceeded for this user
    assert get_exceeded_login_rate_limiter(identifier) is None
    # Test that limiter is exceeded for this user
    login_rate_limiter_user.hit(identifier)
    assert get_exceeded_login_rate_limiter(identifier) == login_rate_limiter_user


def test_get_exceeded_signup_rate_limiter_global():
    signup_rate_limiter.limits = parse_many('1 per 1 minute')
    signup_rate_limiter_email.limits = []
    # Test that the global limiter is not exceeded
    assert get_exceeded_signup_rate_limiter() is None
    # Test that the global limiter is exceeded
    signup_rate_limiter.hit()
    assert get_exceeded_signup_rate_limiter() == signup_rate_limiter


def test_get_exceeded_signup_rate_limiter_scoped():
    identifier = 'foo'
    signup_rate_limiter.limits = parse_many('1 per 1 minute')
    signup_rate_limiter_email.limits = parse_many('1 per 1 minute')
    # Test that the global limiter is still active if not checking for a user
    signup_rate_limiter.hit()
    assert get_exceeded_signup_rate_limiter() == signup_rate_limiter
    # Test that limiter is not exceeded for this user
    assert get_exceeded_signup_rate_limiter(identifier) is None
    # Test that limiter is exceeded for this user
    signup_rate_limiter_email.hit(identifier)
    assert get_exceeded_signup_rate_limiter(identifier) == signup_rate_limiter_email
