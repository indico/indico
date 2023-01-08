# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

import pytest

from indico.modules.events.features.util import set_feature_enabled
from indico.web.flask.templating import get_template_module


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.usefixtures('request_context')
def test_inconsistency_email_to_manager_plaintext(snapshot, dummy_event, dummy_reg):
    set_feature_enabled(dummy_event, 'registration', True)
    dummy_reg.base_price = 1337
    dummy_reg.currency = 'USD'
    template = get_template_module('events/payment/emails/payment_inconsistency_email_to_manager.txt',
                                   event=dummy_event, registration=dummy_reg, amount=404, currency='EUR')
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), 'payment_inconsistency_email_to_manager.txt')
