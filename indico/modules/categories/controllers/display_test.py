# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

import pytest
from flask import request

from indico.modules.categories.controllers.display import RHCategorySearch


@pytest.mark.usefixtures('request_context')
def test_deleted_category_search(dummy_category):
    rh = RHCategorySearch()
    dummy_category.title = 'Dummy'
    request.args = {'q': 'Dum'}
    response = rh._process()
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success']
    assert data['total_count'] == 1
    assert data['categories'][0]['id'] == dummy_category.id

    dummy_category.is_deleted = True
    response = rh._process()
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success']
    assert data['total_count'] == 0
