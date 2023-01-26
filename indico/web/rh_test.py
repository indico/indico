# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from contextlib import nullcontext as does_not_raise
from unittest.mock import MagicMock

import pytest
from werkzeug.exceptions import Forbidden

from indico.core import signals
from indico.web.rh import RH


@pytest.mark.usefixtures('request_context')
def test_before_check_access_signal(mocker):
    mocker.patch.object(RH, '_check_access')
    RH._process_GET = MagicMock()
    rh = RH()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: True):
        rh.process()
        rh._check_access.assert_not_called()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: None):
        rh.process()
        rh._check_access.assert_called_once()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: False):
        with pytest.raises(Forbidden):
            rh.process()


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('signal_rv_1', 'signal_rv_2', 'skipped'), (
    (None,  None,  False),
    (None,  True,  True),
    (True,  True,  True),
))
def test_before_check_access_signal_many_handlers_skipped(mocker, signal_rv_1, signal_rv_2, skipped):
    mocker.patch.object(RH, '_check_access')
    RH._process_GET = MagicMock()
    rh = RH()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: signal_rv_1):
        with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: signal_rv_2):
            rh.process()
            if skipped:
                rh._check_access.assert_not_called()
            else:
                rh._check_access.assert_called_once()


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('signal_rv_1', 'signal_rv_2', 'expectation'), (
    (False, False, pytest.raises(Forbidden)),
    (False, True,  pytest.raises(Forbidden)),
    (False, None,  pytest.raises(Forbidden)),
    (True,  True,  does_not_raise()),
    (None,  None,  does_not_raise()),
))
def test_before_check_access_signal_many_handlers_forbidden(mocker, signal_rv_1, signal_rv_2, expectation):
    RH._process_GET = MagicMock()
    rh = RH()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: signal_rv_1):
        with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: signal_rv_2):
            with expectation:
                rh.process()
