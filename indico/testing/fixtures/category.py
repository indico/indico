# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

import pytest

from indico.modules.categories import Category


@pytest.fixture
def create_category(db):
    """Returns a callable which lets you create dummy events"""

    def _create_category(id_=None, **kwargs):
        kwargs.setdefault('title', u'cat#{}'.format(id_) if id_ is not None else u'dummy')
        kwargs.setdefault('timezone', 'UTC')
        if 'parent' not in kwargs:
            kwargs['parent'] = Category.get_root()
        return Category(id=id_, acl_entries=set(), **kwargs)

    return _create_category


@pytest.fixture
def dummy_category(create_category):
    """Creates a mocked dummy category"""
    return create_category(title='dummy')
