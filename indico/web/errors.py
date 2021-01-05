# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

import traceback
from uuid import uuid4

from flask import g, jsonify, render_template, request, session
from itsdangerous import BadData
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import Forbidden, HTTPException

from indico.core.errors import NoReportError
from indico.legacy.common.cache import GenericCache
from indico.web.util import get_request_info
from indico.web.views import WPError


def render_error(exc, title, message, code, standalone=False):
    _save_error(exc, title, message)
    if _need_json_response():
        return _jsonify_error(exc, title, message, code)
    elif standalone:
        return render_template('standalone_error.html', error_message=title, error_description=message), code
    else:
        try:
            return WPError(title, message).getHTML(), code
        except OperationalError:
            # If the error was caused while connecting the database,
            # rendering the error page fails since e.g. the header/footer
            # templates access the database or calls hooks doing so.
            # In this case we simply fall-back to the standalone error
            # page which does not show the indico UI around the error
            # message but doesn't require any kind of DB connection.
            return render_error(exc, title, message, code, standalone=True)


def load_error_data(uuid):
    return GenericCache('errors').get(uuid)


def _save_error(exc, title, message):
    # Note that `exc` is only used to check if the error should be saved.
    # Any other information is taken from `sys.exc_info()`!
    if 'saved_error_uuid' in g:
        return
    if not _is_error_reportable(exc):
        return
    g.saved_error_uuid = uuid = unicode(uuid4())
    # XXX: keep this outside - it must be called before `get_request_info()`
    # as that function may mess up `sys.exc_info()` in case accessing user
    # details fails
    tb = traceback.format_exc()
    data = {'title': title,
            'message': message,
            'request_info': get_request_info(),
            'traceback': tb,
            'sentry_event_id': g.get('sentry_event_id')}
    GenericCache('errors').set(uuid, data, 7200)


def _need_json_response():
    return request.is_xhr or request.is_json


def _is_error_reporting_opted_out(code):
    header = request.headers.get('X-Indico-No-Report-Error')
    if not header:
        return
    codes = header.split(',')
    return unicode(code) in codes


def _is_error_reportable(exc):
    # client explicitly opted out from reporting this (expected) error
    if hasattr(exc, 'code') and _is_error_reporting_opted_out(exc.code):
        return False
    # error marked as not reportable
    elif isinstance(exc, NoReportError) or getattr(exc, '_disallow_report', False):
        return False
    elif isinstance(exc, BadData):
        # itsdangerous stuff - should only fail if someone tampers with a link
        return False
    elif isinstance(exc, Forbidden):
        # forbidden errors for guests are not reportable
        # for other users: same logic as any other http exception
        return _need_json_response() and session.user is not None
    elif isinstance(exc, HTTPException):
        # http exceptions can only be reported if they occur during
        # an AJAX request - otherwise they are typically caused by
        # users doing something wrong (typing a 404 URL, messing with
        # data, etc)
        return _need_json_response()
    else:
        return True


def _jsonify_error(exc, title, message, code):
    error_data = {
        'title': title,
        'message': message,
        'error_uuid': g.get('saved_error_uuid') if _is_error_reportable(exc) else None,
    }
    response = jsonify(error=error_data)
    response.status_code = code
    return response
