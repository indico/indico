# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from sqlalchemy.exc import IntegrityError

from indico.modules.users.models.export import DataExportRequest, DataExportRequestState


def test_data_export_request_success_must_have_file_1(db, dummy_user):
    DataExportRequest(user=dummy_user, selected_options=[],
                      state=DataExportRequestState.success)

    with pytest.raises(IntegrityError):
        db.session.commit()


def test_data_export_request_success_must_have_file_2(db, dummy_user, dummy_file):
    request = DataExportRequest(user=dummy_user, selected_options=[],
                                state=DataExportRequestState.success,
                                file=dummy_file)

    request.file = None
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_data_export_request_success_must_have_file_3(db, dummy_user):
    request = DataExportRequest(user=dummy_user, selected_options=[],
                                state=DataExportRequestState.none)

    request.state = DataExportRequestState.success
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_data_export_request_enforce_single_request_per_user(db, dummy_user, create_file):
    file = create_file('dummy_file.txt', 'text/plain', 'dummy_context', 'A dummy file')
    DataExportRequest(user=dummy_user, selected_options=[],
                      state=DataExportRequestState.success,
                      file=file)
    db.session.flush()

    file = create_file('dummy_file.txt', 'text/plain', 'dummy_context', 'A dummy file')
    DataExportRequest(user=dummy_user, selected_options=[],
                      state=DataExportRequestState.success,
                      file=file)

    with pytest.raises(IntegrityError):
        db.session.commit()
