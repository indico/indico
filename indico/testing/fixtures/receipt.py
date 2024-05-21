# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

import pytest

from indico.modules.files.models.files import File
from indico.modules.receipts.models.files import ReceiptFile


pytest_plugins = 'indico.modules.receipts.controllers.access_test'


@pytest.fixture
def dummy_receipt_file(db, dummy_event_template, dummy_reg):
    file = File(filename='test.pdf', content_type='application/pdf')
    file.save(('test',), BytesIO(b'hello world'))
    receipt_file = ReceiptFile(registration=dummy_reg, template=dummy_event_template, file=file)
    db.session.flush()
    return receipt_file
