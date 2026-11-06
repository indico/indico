# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

import pytest
from PIL import Image
from sqlalchemy import event
from sqlalchemy.engine import Engine

from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.models.invitations import RegistrationInvitation
from indico.modules.files.models.files import File
from indico.testing.fixtures.storage import MemoryStorage
from indico.testing.util import extract_emails


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


@pytest.fixture
def file_selects():
    selects = []

    def _before_cursor_execute(conn, cursor, statement, *args):
        if 'FROM indico.files' in statement:
            selects.append(statement)

    event.listen(Engine, 'before_cursor_execute', _before_cursor_execute)
    yield selects
    event.remove(Engine, 'before_cursor_execute', _before_cursor_execute)


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


def _invite(client, regform, body):
    url = f'/event/{regform.event_id}/manage/registration/{regform.id}/invitations/invite'
    return client.post(url, json={
        'sender_address': 'sender@example.test',
        'subject': 'Please register',
        'body': f'{body}<p>{{invitation_link}}</p>',
        'first_name': 'Guinea',
        'last_name': 'Pig',
        'affiliation': '',
        'email': 'invitee@example.test',
    })


def _import_invitations(client, regform, body, emails=('invitee@example.test',)):
    url = f'/event/{regform.event_id}/api/registration/{regform.id}/invitations/invite/import'
    return client.post(url, json={
        'sender_address': 'sender@example.test',
        'subject': 'Please register',
        'body': f'{body}<p>{{invitation_link}}</p>',
        'imported': [{'first_name': 'Guinea', 'last_name': 'Pig', 'affiliation': '', 'email': email}
                     for email in emails],
    })


def _send_reminder(client, regform, body):
    regform.invitations.append(RegistrationInvitation(email='invitee@example.test', first_name='Guinea',
                                                      last_name='Pig', affiliation=''))
    url = f'/event/{regform.event_id}/api/registration/{regform.id}/invitations/reminders/send'
    return client.post(url, json={'sender_address': 'sender@example.test', 'subject': 'Please register',
                                  'body': f'{body}<p>{{invitation_link}}</p>', 'bcc_addresses': []})


def _get_html(msg):
    return msg.get_body(('html',)).get_content()


def _get_images(msg):
    return [part for part in msg.walk() if part.get_content_maintype() == 'image']


@pytest.fixture
def other_regform_image_url(manager_client, dummy_event, create_regform, png_image):
    other_regform = create_regform(dummy_event, title='Other form', id=421)
    return _upload_image(manager_client, other_regform, png_image).json['url']


@pytest.fixture
def unrelated_file_url(db, dummy_regform, png_image):
    context = ('event', dummy_regform.event_id, 'regform', dummy_regform.id, 'registration')
    unrelated_file = File.create_from_stream(BytesIO(png_image), 'logo.png', 'image/png', context)
    db.session.refresh(unrelated_file)
    return unrelated_file.signed_download_url


@pytest.fixture
def deleted_image_url(db, manager_client, dummy_regform, png_image):
    url = _upload_image(manager_client, dummy_regform, png_image).json['url']
    db.session.delete(File.query.one())
    db.session.flush()
    return url


def test_invitation_embeds_uploaded_image(manager_client, dummy_regform, png_image, smtp):
    url = _upload_image(manager_client, dummy_regform, png_image).json['url']
    assert _invite(manager_client, dummy_regform, f'<img src="{url}">').status_code == 200
    msg = extract_emails(smtp, one=True, to='invitee@example.test')
    cid = f'email-image-{File.query.one().id}'
    html = _get_html(msg)
    assert f'src="cid:{cid}"' in html
    assert url not in html
    image, = _get_images(msg)
    assert image.get_content_type() == 'image/png'
    assert image['Content-ID'] == f'<{cid}>'
    assert image.get_payload(decode=True) == png_image


def test_invitation_attaches_repeated_image_once(manager_client, dummy_regform, png_image, smtp):
    url = _upload_image(manager_client, dummy_regform, png_image).json['url']
    assert _invite(manager_client, dummy_regform, f'<img src="{url}"><img src="{url}">').status_code == 200
    msg = extract_emails(smtp, one=True, to='invitee@example.test')
    assert _get_html(msg).count('src="cid:') == 2
    assert len(_get_images(msg)) == 1


def test_invitation_keeps_external_images(manager_client, dummy_regform, smtp):
    url = 'https://example.com/logo.png'
    assert _invite(manager_client, dummy_regform, f'<img src="{url}">').status_code == 200
    msg = extract_emails(smtp, one=True, to='invitee@example.test')
    assert f'src="{url}"' in _get_html(msg)
    assert not _get_images(msg)


@pytest.mark.parametrize('send', (_invite, _import_invitations, _send_reminder))
@pytest.mark.parametrize('url_fixture', ('other_regform_image_url', 'unrelated_file_url', 'deleted_image_url'))
def test_send_rejects_images_that_cannot_be_embedded(request, manager_client, dummy_regform, smtp, send, url_fixture):
    url = request.getfixturevalue(url_fixture)
    resp = send(manager_client, dummy_regform, f'<img src="{url}">')
    assert resp.status_code == 422
    assert list(resp.json['webargs_errors']) == ['body']
    assert not smtp.outbox


def test_invitation_import_embeds_uploaded_image(manager_client, dummy_regform, png_image, smtp):
    url = _upload_image(manager_client, dummy_regform, png_image).json['url']
    assert _import_invitations(manager_client, dummy_regform, f'<img src="{url}">').status_code == 200
    msg = extract_emails(smtp, one=True, to='invitee@example.test')
    cid = f'email-image-{File.query.one().id}'
    assert f'src="cid:{cid}"' in _get_html(msg)
    image, = _get_images(msg)
    assert image['Content-ID'] == f'<{cid}>'
    assert image.get_payload(decode=True) == png_image


def test_invitation_preview_keeps_image_url(manager_client, dummy_regform, png_image):
    url = _upload_image(manager_client, dummy_regform, png_image).json['url']
    resp = manager_client.post(f'/event/{dummy_regform.event_id}/manage/registration/{dummy_regform.id}/'
                               'invitation-preview',
                               json={'subject': 'Please register', 'body': f'<img src="{url}">',
                                     'first_name': 'Guinea', 'last_name': 'Pig'})
    assert resp.status_code == 200
    assert f'src="{url}"' in resp.json['body']


def test_reminder_embeds_uploaded_image(manager_client, dummy_regform, png_image, smtp):
    url = _upload_image(manager_client, dummy_regform, png_image).json['url']
    assert _send_reminder(manager_client, dummy_regform, f'<img src="{url}">').status_code == 200
    msg = extract_emails(smtp, one=True, to='invitee@example.test')
    cid = f'email-image-{File.query.one().id}'
    assert f'src="cid:{cid}"' in _get_html(msg)
    image, = _get_images(msg)
    assert image['Content-ID'] == f'<{cid}>'
    assert image.get_payload(decode=True) == png_image


@pytest.mark.parametrize('send', (_invite, _import_invitations, _send_reminder))
def test_send_rejects_images_over_attachment_limit(manager_client, dummy_regform, patch_indico_config, png_image, smtp,
                                                   send):
    patch_indico_config('MAX_EMAIL_ATTACHMENT_SIZE', 1)
    # each image fits within the limit on its own, so only the email as a whole can exceed it
    urls = [_upload_image(manager_client, dummy_regform, png_image + bytes(700 * 1024)).json['url'] for __ in range(2)]
    resp = send(manager_client, dummy_regform, ''.join(f'<img src="{url}">' for url in urls))
    assert resp.status_code == 422
    assert resp.json == {'webargs_errors': {'body': ['Total attachment size too large (max. 1 MB)']}}
    assert not smtp.outbox


def test_image_is_loaded_once_per_request(app_context, manager_client, dummy_regform, png_image, smtp, file_selects,
                                          mocker, monkeypatch):
    url = _upload_image(manager_client, dummy_regform, png_image).json['url']
    file_selects.clear()
    storage_open = mocker.spy(MemoryStorage, 'open')
    # request memoization is disabled in testing mode
    monkeypatch.setitem(app_context.config, 'TESTING', False)
    emails = ('invitee@example.test', 'other-invitee@example.test')
    assert _import_invitations(manager_client, dummy_regform, f'<img src="{url}">', emails=emails).status_code == 200
    assert len(file_selects) == 1
    assert storage_open.call_count == 1
    for email in emails:
        image, = _get_images(extract_emails(smtp, one=True, to=email))
        assert image.get_payload(decode=True) == png_image
