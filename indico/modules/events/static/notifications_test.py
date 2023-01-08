# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

from indico.web.flask.templating import get_template_module


def test_download_notification_email_plaintext(snapshot, dummy_event, dummy_user):
    template = get_template_module('events/static/emails/download_notification_email.txt',
                                   event=dummy_event, link='http://localhost/', user=dummy_user)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), 'download_notification_email.txt')
