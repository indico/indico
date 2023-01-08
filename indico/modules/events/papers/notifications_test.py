# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

from indico.modules.events.papers.models.revisions import PaperRevisionState
from indico.web.flask.templating import get_template_module


def test_paper_judgment_email_plaintext(snapshot, dummy_user, dummy_contribution):
    revision = {'submitter': dummy_user, 'state': PaperRevisionState.accepted,
                'judgment_comment': 'This is a\n comment!'}
    dummy_contribution.id = 0
    template = get_template_module('events/papers/emails/paper_judgment_notification_email.txt',
                                   paper=revision, contribution=dummy_contribution)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), 'paper_judgment_notification_email.txt')
