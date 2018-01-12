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
from mock import MagicMock

from indico.modules.events.payment.models.transactions import PaymentTransaction, TransactionStatus
from indico.modules.events.payment.util import register_transaction


@pytest.mark.parametrize(('new', 'status'), (
    (False, None),
    (True,  TransactionStatus.successful),
    (True,  TransactionStatus.successful),
    (True,  TransactionStatus.pending)
))
def test_register_transaction(mocker, new, status):
    mocker.patch('indico.modules.events.payment.util.db')
    mocker.patch('indico.modules.events.payment.util.notify_registration_state_update')
    cn = mocker.patch.object(PaymentTransaction, 'create_next')
    registration = MagicMock()
    db_transaction = MagicMock(status=status) if new else None
    cn.return_value = db_transaction
    transaction = register_transaction(registration, None, None, None)
    if new:
        assert transaction is db_transaction
    else:
        assert transaction is None
