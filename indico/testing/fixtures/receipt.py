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
from indico.modules.receipts.models.templates import ReceiptTemplate


@pytest.fixture
def dummy_event_template(db, dummy_event):
    tpl = ReceiptTemplate(title='Dummy', event=dummy_event, html='Test')
    db.session.flush()
    return tpl


@pytest.fixture
def dummy_category_template(db, dummy_category):
    tpl = ReceiptTemplate(title='Dummy', category=dummy_category, html='Test')
    db.session.flush()
    return tpl


@pytest.fixture
def create_receipt_file(db):
    """Return a callable that lets you create a registration form."""
    def _create_receipt_file(registration, event_template, published=True, **kwargs):
        file = File(filename='test.pdf', content_type='application/pdf', **kwargs)
        file.save(('test',), BytesIO(b'hello world'))
        receipt_file = ReceiptFile(registration=registration,
                                   template=event_template,
                                   is_published=published,
                                   file=file)
        db.session.flush()
        return receipt_file

    return _create_receipt_file


@pytest.fixture
def dummy_receipt_file(create_receipt_file, dummy_reg, dummy_event_template):
    return create_receipt_file(dummy_reg, dummy_event_template)
