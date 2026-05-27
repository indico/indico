# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import session
from speaklater import make_lazy_string

from indico.core import signals
from indico.modules.events.registration.custom import CustomRegistrationListItem, RegistrationListColumn
from indico.modules.events.registration.lists import RegistrationListGenerator


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


class _TestColumn(CustomRegistrationListItem):
    name = 'test_col'
    title = make_lazy_string(lambda: 'Test Column')

    def load_data(self, registrations):
        return {reg: RegistrationListColumn(content='val', text_value='val') for reg in registrations}


@pytest.fixture
def connected_column():
    """Connect _TestColumn to the registrant_list_items signal for the duration of the test."""
    def _handler(sender, **kwargs):
        yield _TestColumn

    with signals.event.registrant_list_items.connected_to(_handler):
        yield


def test_get_list_export_config_always_has_extra_columns_key(dummy_regform, app_context):
    """get_list_export_config must always return the extra_columns key, even when empty."""
    with app_context.test_request_context():
        gen = RegistrationListGenerator(regform=dummy_regform)
        config = gen.get_list_export_config()

    assert 'extra_columns' in config
    assert isinstance(config['extra_columns'], list)


@pytest.mark.usefixtures('connected_column')
def test_get_list_export_config_includes_selected_extra_column(dummy_regform, app_context):
    """A custom column that the user has enabled appears in get_list_export_config.

    This is the regression test for the bug where extra_item_ids were silently
    discarded in get_list_export_config(), causing signal-added columns to be
    missing from all export formats (CSV, Excel, PDF) even when selected.
    """
    with app_context.test_request_context():
        # Simulate the user having enabled ext__test_col in the column chooser.
        # The config must be set BEFORE constructing the generator because
        # _get_config() is called in __init__.
        session[f'registration_config_{dummy_regform.id}'] = {
            'items': ['ext__test_col', 'state'],
            'filters': {'fields': {}, 'items': {}, 'extra': {}},
        }
        gen = RegistrationListGenerator(regform=dummy_regform)
        config = gen.get_list_export_config()

    assert len(config['extra_columns']) == 1
    assert config['extra_columns'][0].title == 'Test Column'


@pytest.mark.usefixtures('connected_column')
def test_get_list_export_config_excludes_filter_only_column(dummy_regform, app_context):
    """filter_only columns must not appear in extra_columns even when selected."""
    class _FilterOnlyColumn(_TestColumn):
        name = 'filter_col'
        title = 'Filter Only'
        filter_only = True

    def _handler(sender, **kwargs):
        yield _FilterOnlyColumn

    with signals.event.registrant_list_items.connected_to(_handler):
        with app_context.test_request_context():
            session[f'registration_config_{dummy_regform.id}'] = {
                'items': ['ext__filter_col'],
                'filters': {'fields': {}, 'items': {}, 'extra': {}},
            }
            gen = RegistrationListGenerator(regform=dummy_regform)
            config = gen.get_list_export_config()

    assert config['extra_columns'] == []
