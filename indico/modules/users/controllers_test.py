# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import request
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import UnprocessableEntity


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
