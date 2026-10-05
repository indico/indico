# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import request, session
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import UnprocessableEntity

from indico.core import signals


@pytest.mark.usefixtures('request_context')
def test_invalid_request():
    """Test data export request with invalid options."""
    from indico.modules.users.controllers import RHUserDataExportAPI
    rh = RHUserDataExportAPI()
    request.method = 'POST'
    request.form = MultiDict({'options': 'test'})

    with pytest.raises(UnprocessableEntity):
        rh._process()


@pytest.mark.usefixtures('request_context')
def test_user_data_request(mocker, dummy_user):
    from indico.modules.users.controllers import RHUserDataExportAPI
    from indico.modules.users.models.export import DataExportOptions, DataExportRequestState
    from indico.modules.users.tasks import export_user_data
    task = mocker.patch.object(export_user_data, 'delay')

    rh = RHUserDataExportAPI()
    request.method = 'POST'
    request.form = MultiDict({'options': DataExportOptions.contribs.name, 'include_files': True})
    rh.user = dummy_user

    response = rh._process()
    task.assert_called()
    assert response == {'state': DataExportRequestState.running.name}


def test_user_search_results_filtered_by_all_handlers(app_context, create_user, dummy_user):
    from indico.modules.users.controllers import RHUserSearch
    alice = create_user(1, first_name='Alice', last_name='Searchable')
    bob = create_user(2, first_name='Bob', last_name='Searchable')
    create_user(3, first_name='Carol', last_name='Searchable')

    def _hide_alice(sender, results, **kwargs):
        results[:] = [r for r in results if r['id'] != alice.id]

    def _hide_bob(sender, results, **kwargs):
        results[:] = [r for r in results if r['id'] != bob.id]

    with app_context.test_request_context(query_string={'last_name': 'Searchable'}):
        session.set_session_user(dummy_user)
        with (signals.users.filter_user_search_results.connected_to(_hide_alice),
              signals.users.filter_user_search_results.connected_to(_hide_bob)):
            response = RHUserSearch()._process()

    assert [u['full_name'] for u in response.json['users']] == ['Carol Searchable']
