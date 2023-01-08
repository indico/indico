# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

import pytest

from indico.modules.events.agreements.models.agreements import AgreementState
from indico.web.flask.templating import get_template_module


pytest_plugins = 'indico.modules.events.agreements.testing.fixtures'


@pytest.mark.parametrize(('state', 'reason', 'snapshot_name'), (
    (AgreementState.rejected, '', 'email_to_managers_rejected_no_reason.txt'),
    (AgreementState.accepted, '', 'email_to_managers_accepted_no_reason.txt'),
    (AgreementState.accepted, 'I accept this.\n:)', 'email_to_managers_accepted_reason.txt'),
    (AgreementState.rejected, 'I do not accept this.\n>:(', 'email_to_managers_rejected_reason.txt'),
))
@pytest.mark.usefixtures('request_context')
def test_signature_email_to_manager_plaintext(snapshot, dummy_agreement, state, reason, snapshot_name):
    dummy_agreement.state = state
    dummy_agreement.reason = reason
    template = get_template_module('events/agreements/emails/new_signature_email_to_manager.txt',
                                   agreement=dummy_agreement)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), snapshot_name)
