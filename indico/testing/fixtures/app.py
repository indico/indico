# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import pytest

from indico.web.flask.app import make_app


@pytest.fixture(scope='session')
def app():
    """Creates the flask app"""
    return make_app(set_path=True, testing=True)


@pytest.yield_fixture(autouse=True)
def app_context(app):
    """Creates a flask app context"""
    with app.app_context():
        yield app


@pytest.yield_fixture
def request_context(app_context):
    """Creates a flask request context"""
    with app_context.test_request_context():
        yield
