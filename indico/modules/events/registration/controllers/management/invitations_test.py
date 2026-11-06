# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

import pytest
from PIL import Image

from indico.modules.events.features.util import set_feature_enabled
from indico.modules.files.models.files import File


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.fixture(autouse=True)
def _configure_dummy_event(dummy_event):
    set_feature_enabled(dummy_event, 'registration', True)


@pytest.fixture
def manager_client(test_client, dummy_user, dummy_event, no_csrf_check):
    dummy_event.update_principal(dummy_user, full_access=True)
    with test_client.session_transaction() as sess:
        sess.set_session_user(dummy_user)
    return test_client


@pytest.fixture
def png_image():
    data = BytesIO()
    Image.new('RGB', (4, 4), 'red').save(data, 'PNG')
    return data.getvalue()


def _upload_image(client, regform, data, filename='logo.png'):
    url = f'/event/{regform.event_id}/api/registration/{regform.id}/invitations/image/upload'
    return client.post(url, data={'upload': (BytesIO(data), filename)}, headers={'X-Requested-With': 'XMLHttpRequest'})


def test_image_upload(manager_client, dummy_regform, png_image):
    resp = _upload_image(manager_client, dummy_regform, png_image)
    assert resp.status_code == 200
    image = File.query.one()
    assert resp.json['url'].startswith(f'http://localhost/files/{image.uuid}/download?token=')
    assert image.content_type == 'image/png'
    with image.open() as f:
        assert f.read() == png_image


def test_image_upload_ignores_filename_extension(manager_client, dummy_regform, png_image):
    resp = _upload_image(manager_client, dummy_regform, png_image, 'logo.txt')
    assert resp.status_code == 200
    assert File.query.one().content_type == 'image/png'


@pytest.mark.parametrize(('data', 'filename'), (
    (b'definitely not an image', 'logo.png'),
    (b'<svg xmlns="http://www.w3.org/2000/svg"/>', 'logo.svg'),
))
def test_image_upload_rejects_non_images(manager_client, dummy_regform, data, filename):
    resp = _upload_image(manager_client, dummy_regform, data, filename)
    assert resp.status_code == 422
    assert not File.query.has_rows()


@pytest.mark.parametrize(('setting', 'error'), (
    ('MAX_UPLOAD_FILE_SIZE', 'The uploaded file is too large'),
    ('MAX_EMAIL_ATTACHMENT_SIZE', 'The image is too large to be sent by email (max. 1 MB)'),
))
def test_image_upload_rejects_images_over_size_limits(manager_client, dummy_regform, patch_indico_config, png_image,
                                                      setting, error):
    patch_indico_config(setting, 1)
    resp = _upload_image(manager_client, dummy_regform, png_image + bytes(1024 * 1024))
    assert resp.status_code == 422
    assert resp.json == {'webargs_errors': {'upload': [error]}}
    assert not File.query.has_rows()


def test_image_upload_rejects_decompression_bombs(manager_client, dummy_regform, monkeypatch, png_image):
    monkeypatch.setattr(Image, 'MAX_IMAGE_PIXELS', 1)
    resp = _upload_image(manager_client, dummy_regform, png_image)
    assert resp.status_code == 422
    assert not File.query.has_rows()


@pytest.mark.parametrize('logged_in', (False, True))
@pytest.mark.usefixtures('no_csrf_check')
def test_image_upload_requires_manager(test_client, dummy_user, dummy_regform, png_image, logged_in):
    if logged_in:
        with test_client.session_transaction() as sess:
            sess.set_session_user(dummy_user)
    resp = _upload_image(test_client, dummy_regform, png_image)
    assert resp.status_code == 403
    assert not File.query.has_rows()
