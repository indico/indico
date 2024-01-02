# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from flask import abort, redirect, request
from werkzeug.exceptions import NotFound

from indico.modules.categories.models.legacy_mapping import LegacyCategoryMapping
from indico.web.flask.util import url_for
from indico.web.rh import RHSimple


@RHSimple.wrap_function
def compat_category(legacy_category_id, path=None):
    if not re.match(r'^\d+l\d+$', legacy_category_id):
        abort(404)
    mapping = LegacyCategoryMapping.query.filter_by(legacy_category_id=legacy_category_id).first()
    if mapping is None:
        raise NotFound(f'Legacy category {legacy_category_id} does not exist')
    view_args = request.view_args.copy()
    view_args['legacy_category_id'] = mapping.category_id
    # To create the same URL with the proper ID we take advantage of the
    # fact that the legacy endpoint works perfectly fine with proper IDs
    # too (you can pass an int for a string argument), but due to the
    # weight of the `int` converter used for new endpoints, the URL will
    # then be handled by the proper endpoint instead of this one.
    build_args = request.args.to_dict() | view_args
    return redirect(url_for(request.endpoint, **build_args), 301)
