# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from __future__ import absolute_import, unicode_literals

from flask import g, render_template, jsonify, request, session, has_request_context
from markupsafe import Markup


def inject_js(js):
    """Injects JavaScript into the current page.

    :param js: Code wrapped in a ``<script>`` tag.
    """
    if 'injected_js' not in g:
        g.injected_js = []
    g.injected_js.append(Markup(js))


def jsonify_template(template, _render_func=render_template, **context):
    """Returns a json response containing a rendered template"""
    html = _render_func(template, **context)
    js = None
    if 'injected_js' in g:
        js = g.injected_js
        del g.injected_js
    return jsonify(html=html, js=js)


def jsonify_data(flash=True, **json_data):
    """Returns a json response with some default fields.

    This behaves similar to :func:`~flask.jsonify`, but includes
    ``success=True`` and flashed messages by default.

    :param flash: if the json data should contain flashed messages
    :param json_data: the data to include in the json response
    """
    json_data.setdefault('success', True)
    if flash:
        json_data['flashed_messages'] = render_template('flashed_messages.html')
    return jsonify(**json_data)


def _format_request_data(data, hide_passwords):
    if not hasattr(data, 'iterlists'):
        data = ((k, [v]) for k, v in data.iteritems())
    else:
        data = data.iterlists()
    rv = {}
    for key, values in data:
        if hide_passwords and 'password' in key:
            values = [v if not v else '<{} chars hidden>'.format(len(v)) for v in values]
        rv[key] = values if len(values) != 1 else values[0]
    return rv


def get_request_info(hide_passwords=True):
    """Gets various information about the current HTTP request.

    This is especially useful for logging purposes where you want
    as many information as possible.

    :param hide_passwords: Hides the actual value of POST fields
                           if their name contains ``password``.

    :return: a dictionary containing request information, or ``None``
             when called outside a request context
    """
    if not has_request_context():
        return None
    return {
        'id': request.id,
        'url': request.url,
        'endpoint': request.url_rule.endpoint if request.url_rule else None,
        'method': request.method,
        'rh': g.rh.__class__.__name__ if 'rh' in g else None,
        'user': repr(session.user),
        'ip': request.remote_addr,
        'user_agent': unicode(request.user_agent),
        'referrer': request.referrer,
        'data': {
            'url': _format_request_data(request.view_args, False),
            'get': _format_request_data(request.args, False),
            'post': _format_request_data(request.form, hide_passwords),
            'json': request.get_json(silent=True),
            'headers': _format_request_data(request.headers, False),
        }
    }
