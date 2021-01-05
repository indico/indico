# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

import pytest
from flask import session
from werkzeug.exceptions import Forbidden

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.attachments.controllers.display.event import RHDownloadEventAttachment
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.events.controllers.base import AccessKeyRequired, RegistrationRequired
from indico.util.date_time import now_utc


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def _make_attachment(user, obj):
    folder = AttachmentFolder(title='dummy_folder', description='a dummy folder')
    file = AttachmentFile(user=user, filename='dummy_file.txt', content_type='text/plain')
    attachment = Attachment(folder=folder, user=user, title='dummy_attachment', type=AttachmentType.file, file=file)
    attachment.folder.object = obj
    attachment.file.save(BytesIO(b'hello world'))
    return attachment


@pytest.fixture
def attachment_access_test_env(request_context, dummy_user, dummy_event, dummy_session, create_contribution):
    session.user = dummy_user
    session_contrib = create_contribution(dummy_event, 'Session Contrib', session=dummy_session)
    standalone_contrib = create_contribution(dummy_event, 'Standalone Contrib')
    event_attachment = _make_attachment(dummy_user, dummy_event)
    session_attachment = _make_attachment(dummy_user, dummy_session)
    session_contrib_attachment = _make_attachment(dummy_user, session_contrib)
    standalone_contrib_attachment = _make_attachment(dummy_user, standalone_contrib)

    rh = RHDownloadEventAttachment()
    rh.event = dummy_event

    def assert_access_check(attachment, accessible=True, expected_exc=Forbidden):
        __tracebackhide__ = True
        rh.attachment = attachment
        if accessible:
            rh._check_access()
        else:
            with pytest.raises(expected_exc) as exc_info:
                rh._check_access()
            assert exc_info.type is expected_exc

    yield type('AttachmentAccessTestEnv', (object,), {
        'event': dummy_event,
        'session': dummy_session,
        'standalone_contrib': standalone_contrib,
        'session_contrib': session_contrib,
        'event_attachment': event_attachment,
        'session_attachment': session_attachment,
        'session_contrib_attachment': session_contrib_attachment,
        'standalone_contrib_attachment': standalone_contrib_attachment,
        'assert_access_check': staticmethod(assert_access_check),
    })


@pytest.mark.parametrize(
    ('event_prot', 'session_prot', 'session_contrib_prot', 'standalone_contrib_prot', 'accessible'), (
        # Everything should be accessible in a public event
        ('public', None, None, None, ('event', 'session', 'standalone_contrib', 'session_contrib')),
        # Protecting the event should restrict everything
        ('protected', None, None, None, ()),
        # A public session in a protected event should allow access to its contents
        ('protected', 'public', None, None, ('session', 'session_contrib')),
        # Session access should not work if the contribution is protected
        ('protected', 'public', 'protected', None, ('session',)),
        # Public contribution access should be possible
        ('protected', 'protected', 'public', 'public', ('session_contrib', 'standalone_contrib')),
    )
)
def test_access_checks(db, attachment_access_test_env, event_prot, session_prot, session_contrib_prot,
                       standalone_contrib_prot, accessible):
    env = attachment_access_test_env
    env.event.protection_mode = ProtectionMode[event_prot]
    env.session.protection_mode = ProtectionMode[session_prot or 'inheriting']
    env.session_contrib.protection_mode = ProtectionMode[session_contrib_prot or 'inheriting']
    env.standalone_contrib.protection_mode = ProtectionMode[standalone_contrib_prot or 'inheriting']
    db.session.flush()
    env.assert_access_check(env.event_attachment, 'event' in accessible)
    env.assert_access_check(env.session_attachment, 'session' in accessible)
    env.assert_access_check(env.standalone_contrib_attachment, 'standalone_contrib' in accessible)
    env.assert_access_check(env.session_contrib_attachment, 'session_contrib' in accessible)


def test_self_protected(db, attachment_access_test_env):
    env = attachment_access_test_env
    env.event_attachment.protection_mode = ProtectionMode.protected
    env.session_attachment.protection_mode = ProtectionMode.protected
    env.standalone_contrib_attachment.protection_mode = ProtectionMode.protected
    env.session_contrib_attachment.protection_mode = ProtectionMode.protected
    db.session.flush()
    env.assert_access_check(env.event_attachment, False)
    env.assert_access_check(env.session_attachment, False)
    env.assert_access_check(env.standalone_contrib_attachment, False)
    env.assert_access_check(env.session_contrib_attachment, False)


def test_access_key(db, attachment_access_test_env):
    env = attachment_access_test_env
    env.event.protection_mode = ProtectionMode.protected
    env.event.access_key = 'secret'
    db.session.flush()
    env.assert_access_check(env.event_attachment, False, AccessKeyRequired)
    env.assert_access_check(env.session_attachment, False, AccessKeyRequired)
    env.assert_access_check(env.standalone_contrib_attachment, False, AccessKeyRequired)
    env.assert_access_check(env.session_contrib_attachment, False, AccessKeyRequired)


def test_only_registered(db, dummy_regform, attachment_access_test_env):
    env = attachment_access_test_env
    env.event.protection_mode = ProtectionMode.protected
    env.event.public_regform_access = True
    env.event.update_principal(dummy_regform, read_access=True)
    dummy_regform.start_dt = now_utc()
    db.session.flush()
    env.assert_access_check(env.event_attachment, False, RegistrationRequired)
    env.assert_access_check(env.session_attachment, False, RegistrationRequired)
    env.assert_access_check(env.standalone_contrib_attachment, False, RegistrationRequired)
    env.assert_access_check(env.session_contrib_attachment, False, RegistrationRequired)
