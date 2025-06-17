# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

import pytest
from flask import session

from indico.modules.events.operations import clone_event
from indico.modules.events.settings import event_language_settings


@pytest.mark.usefixtures('request_context')
def test_language_settings_cloned(dummy_event, app, dummy_user):
    with app.test_request_context():
        # Set up language settings
        event_language_settings.set(dummy_event, 'default_locale', 'fr_FR')
        event_language_settings.set(dummy_event, 'enforce_locale', True)
        event_language_settings.set(dummy_event, 'supported_locales', ['es_ES', 'en_GB'])

        session.set_session_user(dummy_user)
        start_dt = datetime(2022, 11, 11, 13, 37)
        cloners = set()
        n_occurrence = 1

        # Clone the event
        new_event = clone_event(dummy_event, n_occurrence, start_dt, cloners)
        # Assert that the language settings are cloned correctly
        assert event_language_settings.get(new_event, 'default_locale') == 'fr_FR'
        assert event_language_settings.get(new_event, 'enforce_locale')
        assert event_language_settings.get(new_event, 'supported_locales') == ['es_ES', 'en_GB']
