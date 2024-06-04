# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO
from zipfile import ZipFile

import pytest

from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.modules.receipts.settings import receipts_settings


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


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


@pytest.mark.parametrize('owner_type', ('event', 'category'))
@pytest.mark.parametrize(('method', 'url', 'admin_only'), (
    ('GET',    '/admin/receipts/', True),
    # event
    ('GET',    '/{prefix}/manage/receipts/', False),
    ('GET',    '/{prefix}/manage/receipts/add', False),
    ('POST',   '/{prefix}/manage/receipts/live-preview', False),
    ('GET',    '/{prefix}/manage/receipts/{tpl_id}/', False),
    ('GET',    '/{prefix}/manage/receipts/{tpl_id}/preview-template', False),
    ('POST',   '/{prefix}/manage/receipts/{tpl_id}/clone', False),
    ('PATCH',  '/{prefix}/manage/receipts/{tpl_id}/', False),
    ('DELETE', '/{prefix}/manage/receipts/{tpl_id}/', False),
))
@pytest.mark.usefixtures('no_csrf_check')
@pytest.mark.usefixtures('request_context')
def test_basic_access_checks(test_client, dummy_user, create_user, dummy_event, dummy_category, dummy_event_template,
                             dummy_category_template, owner_type, method, url, admin_only):
    if owner_type == 'event':
        prefix = f'event/{dummy_event.id}'
        tpl_id = dummy_event_template.id
    elif owner_type == 'category':
        prefix = f'category/{dummy_category.id}'
        tpl_id = dummy_category_template.id
    url = url.format(prefix=prefix, tpl_id=tpl_id)
    # guest
    resp = test_client.open(url, method=method, headers={'Content-type': 'application/json'})
    assert resp.status_code == 403
    # user
    dummy_event.update_principal(dummy_user, full_access=True)
    dummy_category.update_principal(dummy_user, full_access=True)
    with test_client.session_transaction() as sess:
        sess.set_session_user(dummy_user)
    resp = test_client.open(url, method=method, headers={'Content-type': 'application/json'})
    assert resp.status_code == 403
    # authorized user
    receipts_settings.acls.set('authorized_users', {dummy_user})
    resp = test_client.open(url, method=method, headers={'Content-type': 'application/json'})
    if admin_only:
        assert resp.status_code == 403
    else:
        assert resp.status_code != 403
    # admin user
    admin_user = create_user(100, admin=True)
    with test_client.session_transaction() as sess:
        sess.set_session_user(admin_user)
    resp = test_client.open(url, method=method, headers={'Content-type': 'application/json'})
    assert resp.status_code != 403


@pytest.mark.usefixtures('no_csrf_check')
def test_bulk_download_receipts(test_client, dummy_user, dummy_event, create_event, dummy_receipt_file):
    """Make sure one cannot download receipts from a different event."""
    dummy_user.is_admin = True
    with test_client.session_transaction() as sess:
        sess.set_session_user(dummy_user)
    url = '/event/{event_id}/manage/receipts/export/receipts.zip'
    # retrieve file via the correct event
    resp = test_client.post(url.format(event_id=dummy_event.id), json={'receipt_ids': [dummy_receipt_file.file_id]})
    assert resp.status_code == 200
    with ZipFile(BytesIO(resp.data)) as file:
        assert len(file.namelist()) == 1
    resp.close()
    # attempt to retrieve file via another event
    other_event = create_event()
    resp = test_client.post(url.format(event_id=other_event.id), json={'receipt_ids': [dummy_receipt_file.file_id]})
    assert resp.status_code == 200  # we just filter receipt ids within the event so the request succeeds
    with ZipFile(BytesIO(resp.data)) as file:
        assert not file.namelist()  # but the zip file must be empty!
    resp.close()
