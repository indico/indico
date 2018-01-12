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

import re

from flask import abort, redirect, request
from werkzeug.exceptions import NotFound

from indico.modules.categories import LegacyCategoryMapping
from indico.web.flask.util import url_for
from indico.web.rh import RHSimple


@RHSimple.wrap_function
def compat_category(legacy_category_id, path=None):
    if not re.match(r'^\d+l\d+$', legacy_category_id):
        abort(404)
    mapping = LegacyCategoryMapping.find_first(legacy_category_id=legacy_category_id)
    if mapping is None:
        raise NotFound('Legacy category {} does not exist'.format(legacy_category_id))
    view_args = request.view_args.copy()
    view_args['legacy_category_id'] = mapping.category_id
    # To create the same URL with the proper ID we take advantage of the
    # fact that the legacy endpoint works perfectly fine with proper IDs
    # too (you can pass an int for a string argument), but due to the
    # weight of the `int` converter used for new endpoints, the URL will
    # then be handled by the proper endpoint instead of this one.
    return redirect(url_for(request.endpoint, **dict(request.args.to_dict(), **view_args)), 301)
