# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

import pytest

from indico.web.flask.templating import get_template_module


@pytest.mark.parametrize(('test_file', 'affiliation'), (
    ('profile_registered_admins_affil.txt', 'Illuminyati'),
    ('profile_registered_admins.txt', None),
))
def test_profile_registered_email_plaintext(snapshot, dummy_user, test_file, affiliation):
    dummy_user.affiliation = affiliation
    template = get_template_module('users/emails/profile_registered_admins.txt',
                                   user=dummy_user)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), test_file)


@pytest.mark.parametrize(('test_file', 'comment', 'affiliation'), (
    ('profile_requested_admins_comment.txt', 'A comment.\nMeow!', None),
    ('profile_requested_admins_affil_comment.txt', 'A comment.\nMeow!', 'Illuminyati'),
    ('profile_requested_admins_affil.txt', None, 'Illuminyati'),
    ('profile_requested_admins.txt', None, None),
))
def test_profile_requested_email_plaintext(snapshot, dummy_user, comment, affiliation, test_file):
    dummy_user.affiliation = affiliation
    req = {'comment': comment, 'user_data': dummy_user, 'email': 'cat@meow.cat'}
    template = get_template_module('users/emails/profile_requested_admins.txt',
                                   req=req)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), test_file)


@pytest.mark.usefixtures('request_context')
def test_reg_req_accepted_email_plaintext(snapshot, dummy_user):
    template = get_template_module('users/emails/registration_request_accepted.txt',
                                   user=dummy_user)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), 'registration_request_accepted.txt')


def test_reg_req_rejected_email_plaintext(snapshot, dummy_user):
    req = {'user_data': dummy_user}
    template = get_template_module('users/emails/registration_request_rejected.txt',
                                   req=req)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), 'registration_request_rejected.txt')
