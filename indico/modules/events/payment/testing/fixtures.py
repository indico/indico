# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.modules.events.payment.models.transactions import PaymentTransaction, TransactionStatus


@pytest.fixture
def create_transaction():
    """Returns a callable which lets you create transactions"""

    def _create_transaction(status, **params):
        params.setdefault('amount', 10)
        params.setdefault('currency', 'USD')
        params.setdefault('provider', '_manual')
        params.setdefault('data', {})
        return PaymentTransaction(status=status, **params)

    return _create_transaction


@pytest.fixture
def dummy_transaction(create_transaction):
    """Gives you a dummy successful transaction"""
    return create_transaction(status=TransactionStatus.successful)
