# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
