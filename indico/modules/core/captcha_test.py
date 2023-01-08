# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import session

from .captcha import _verify_captcha, generate_captcha_challenge


class _MockRandom:
    @staticmethod
    def choices(pop, k):
        return list('6970')


@pytest.mark.filterwarnings('ignore:.*removed in Pillow 10.*:DeprecationWarning')
def test_generate_captcha_challenge(monkeypatch):
    # this test exists mainly to fail in case the captcha lib isn't updated
    # to stop using deprecated Pillow features by the time they remove them
    # for good in in 2023
    monkeypatch.setattr('indico.modules.core.captcha.random', _MockRandom)
    data, answer = generate_captcha_challenge()
    assert set(data) == {'image', 'audio'}
    assert answer == '6970'


@pytest.mark.usefixtures('request_context')
def test_verify_captcha():
    assert not _verify_captcha('')
    session['captcha_state'] = '7234'
    assert not _verify_captcha('')
    assert not _verify_captcha('0000')
    assert not _verify_captcha('4327')
    assert _verify_captcha('1234')
    assert _verify_captcha('7234')
