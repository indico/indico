# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from unittest.mock import MagicMock

import pytest

from indico.modules.events.payment.models.transactions import (DoublePaymentTransaction, IgnoredTransactionAction,
                                                               InvalidManualTransactionAction, InvalidTransactionAction,
                                                               InvalidTransactionStatus, PaymentTransaction,
                                                               TransactionAction, TransactionStatus,
                                                               TransactionStatusTransition)
from indico.testing.util import extract_logs


pytest_plugins = 'indico.modules.events.payment.testing.fixtures'


@pytest.fixture
def patch_transition_methods(mocker):
    mocker.patch.object(TransactionStatusTransition, '_next_from_initial')
    mocker.patch.object(TransactionStatusTransition, '_next_from_successful')
    mocker.patch.object(TransactionStatusTransition, '_next_from_pending')


@pytest.fixture
def creation_params():
    return {'registration': MagicMock(transaction=None),
            'amount': 10,
            'currency': 'USD',
            'action': TransactionAction.complete,
            'provider': 'le-provider'}


# ======================================================================================================================
# TransactionStatusTransition tests
# ======================================================================================================================

@pytest.mark.usefixtures('patch_transition_methods')
@pytest.mark.parametrize(('status', 'expected_transition'), (
    (None,                         'initial'),
    (TransactionStatus.successful, 'successful'),
    (TransactionStatus.cancelled,  'initial'),
    (TransactionStatus.failed,     'initial'),
    (TransactionStatus.pending,    'pending'),
    (TransactionStatus.rejected,   'initial'),
))
def test_next(create_transaction, status, expected_transition):
    transaction = create_transaction(status) if status else None
    TransactionStatusTransition.next(transaction, TransactionAction.complete,  '_manual')
    if expected_transition == 'initial':
        assert TransactionStatusTransition._next_from_initial.called
    elif expected_transition == 'successful':
        assert TransactionStatusTransition._next_from_successful.called
    elif expected_transition == 'pending':
        assert TransactionStatusTransition._next_from_pending.called


@pytest.mark.usefixtures('patch_transition_methods')
@pytest.mark.parametrize(('provider', 'manual'), (
    (None,   True),
    ('manual',    False),
    ('whatever',  False),
))
def test_next_providers(create_transaction, provider, manual):
    action = TransactionAction.complete
    initial_transaction = create_transaction(TransactionStatus.cancelled)
    successful_transaction = create_transaction(TransactionStatus.successful)
    pending_transaction = create_transaction(TransactionStatus.pending)
    # Test initial statuses
    TransactionStatusTransition.next(initial_transaction, action, provider)
    TransactionStatusTransition._next_from_initial.assert_called_with(action, manual)
    # Test successful statuses
    TransactionStatusTransition.next(successful_transaction, action, provider)
    TransactionStatusTransition._next_from_successful.assert_called_with(action, manual)
    # Test pending statuses
    TransactionStatusTransition.next(pending_transaction, action, provider)
    TransactionStatusTransition._next_from_pending.assert_called_with(action, manual)


def test_next_invalid():
    transaction = MagicMock(status=1337)
    with pytest.raises(InvalidTransactionStatus):
        TransactionStatusTransition.next(transaction, TransactionAction.complete, '')


@pytest.mark.parametrize(('action', 'manual', 'expected'), (
    (TransactionAction.complete, True,  TransactionStatus.successful),
    (TransactionAction.cancel,   True,  IgnoredTransactionAction),
    (TransactionAction.pending,  True,  InvalidManualTransactionAction),
    (TransactionAction.reject,   True,  InvalidManualTransactionAction),
    (TransactionAction.complete, False, TransactionStatus.successful),
    (TransactionAction.cancel,   False, InvalidTransactionAction),
    (TransactionAction.pending,  False, TransactionStatus.pending),
    (TransactionAction.reject,   False, IgnoredTransactionAction),
))
def test_next_from_initial(action, manual, expected):
    if isinstance(expected, TransactionStatus):
        assert TransactionStatusTransition._next_from_initial(action, manual) == expected
    else:
        with pytest.raises(expected):
            TransactionStatusTransition._next_from_initial(action, manual)


@pytest.mark.parametrize(('action', 'manual', 'expected'), (
    (TransactionAction.complete, True,  IgnoredTransactionAction),
    (TransactionAction.cancel,   True,  TransactionStatus.cancelled),
    (TransactionAction.pending,  True,  InvalidManualTransactionAction),
    (TransactionAction.reject,   True,  InvalidManualTransactionAction),
    (TransactionAction.complete, False, DoublePaymentTransaction),
    (TransactionAction.cancel,   False, InvalidTransactionAction),
    (TransactionAction.pending,  False, IgnoredTransactionAction),
    (TransactionAction.reject,   False, IgnoredTransactionAction),
))
def test_next_from_successful(action, manual, expected):
    if isinstance(expected, TransactionStatus):
        assert TransactionStatusTransition._next_from_successful(action, manual) == expected
    else:
        with pytest.raises(expected):
            TransactionStatusTransition._next_from_successful(action, manual)


@pytest.mark.parametrize(('action', 'manual', 'expected'), (
    (TransactionAction.complete, True,  IgnoredTransactionAction),
    (TransactionAction.cancel,   True,  TransactionStatus.cancelled),
    (TransactionAction.pending,  True,  InvalidManualTransactionAction),
    (TransactionAction.reject,   True,  InvalidManualTransactionAction),
    (TransactionAction.complete, False, TransactionStatus.successful),
    (TransactionAction.cancel,   False, InvalidTransactionAction),
    (TransactionAction.pending,  False, IgnoredTransactionAction),
    (TransactionAction.reject,   False, TransactionStatus.rejected),
))
def test_next_from_pending(action, manual, expected):
    if isinstance(expected, TransactionStatus):
        assert TransactionStatusTransition._next_from_pending(action, manual) == expected
    else:
        with pytest.raises(expected):
            TransactionStatusTransition._next_from_pending(action, manual)


# ======================================================================================================================
# PaymentTransaction tests
# ======================================================================================================================

@pytest.mark.parametrize(('provider', 'expected'), (
    ('_manual', True),
    ('manual', False),
    ('le-provider', False),
))
def test_manual(dummy_transaction, provider, expected):
    dummy_transaction.provider = provider
    assert dummy_transaction.is_manual == expected


def test_create_next(creation_params):
    transaction = PaymentTransaction.create_next(**creation_params)
    assert isinstance(transaction, PaymentTransaction)


@pytest.mark.parametrize('exception', (
    InvalidTransactionStatus,
    InvalidManualTransactionAction,
    InvalidTransactionAction,
    IgnoredTransactionAction,
))
def test_create_next_with_exception(caplog, mocker, creation_params, exception):
    mocker.patch.object(TransactionStatusTransition, 'next')
    TransactionStatusTransition.next.side_effect = exception('TEST_EXCEPTION')
    transaction = PaymentTransaction.create_next(**creation_params)
    log = extract_logs(caplog, one=True, name='indico.payment')
    assert transaction is None
    assert 'TEST_EXCEPTION' in log.message
    if log.exc_info:
        assert log.exc_info[0] == exception
