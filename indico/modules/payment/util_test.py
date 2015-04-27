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

import pytest
from flask import session, request
from mock import MagicMock

from indico.modules.payment.models.transactions import PaymentTransaction, TransactionStatus
from indico.modules.payment.util import get_registrant_params, register_transaction


@pytest.mark.parametrize(('new', 'double', 'status'), (
    (False, False, None),
    (True,  True,  TransactionStatus.successful),
    (True,  False, TransactionStatus.successful),
    (True,  False, TransactionStatus.pending)
))
def test_register_transaction(mocker, new, double, status):
    mocker.patch('indico.modules.payment.util.db')
    ndp = mocker.patch('indico.modules.payment.util.notify_double_payment')
    npc = mocker.patch('indico.modules.payment.util.notify_payment_confirmation')
    cn = mocker.patch.object(PaymentTransaction, 'create_next')
    db_transaction = MagicMock(status=status) if new else None
    cn.return_value = db_transaction, double
    transaction = register_transaction(None, None, None, None)
    if new:
        assert transaction is db_transaction
        assert ndp.called == double
        assert npc.called == (transaction.status == TransactionStatus.successful)
    else:
        assert transaction is None
        assert not ndp.called
        assert not npc.called


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('user', 'params'), (
    (True,  {}),
    (False, {'registrantId': '0', 'authkey': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}),
))
def test_get_registrant_params(dummy_user, user, params):
    request.values = params
    if user:
        session.user = dummy_user.user
    assert get_registrant_params() == params
