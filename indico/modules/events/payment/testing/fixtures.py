# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.payment.models.transactions import PaymentTransaction, TransactionStatus


@pytest.fixture
def create_transaction():
    """Return a callable which lets you create transactions."""

    def _create_transaction(status, **params):
        params.setdefault('amount', 10)
        params.setdefault('currency', 'USD')
        params.setdefault('provider', '_manual')
        params.setdefault('data', {})
        return PaymentTransaction(status=status, **params)

    return _create_transaction


@pytest.fixture
def dummy_transaction(create_transaction):
    """Return a dummy successful transaction."""
    return create_transaction(status=TransactionStatus.successful)
