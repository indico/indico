# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

from datetime import datetime

from flask import g, has_request_context, jsonify, render_template, request, session
from itsdangerous import Signer
from markupsafe import Markup
from werkzeug.exceptions import ImATeapot
from werkzeug.urls import url_decode, url_encode, url_parse, url_unparse

from indico.util.i18n import _
from indico.web.flask.templating import get_template_module


def inject_js(js):
    """Inject JavaScript into the current page.

    :param js: Code wrapped in a ``<script>`` tag.
    """
    if 'injected_js' not in g:
        g.injected_js = []
    g.injected_js.append(Markup(js))


def _pop_injected_js():
    js = None
    if 'injected_js' in g:
        js = g.injected_js
        del g.injected_js
    return js


def jsonify_form(form, fields=None, submit=None, back=None, back_url=None, back_button=True, disabled_until_change=True,
                 disabled_fields=(), form_header_kwargs=None, skip_labels=False, save_reminder=False,
                 footer_align_right=False, disable_if_locked=True, message=None):
    """Return a json response containing a rendered WTForm.

    This is shortcut to the ``simple_form`` jinja macro to avoid
    adding new templates that do nothing besides importing and
    calling this macro.

    :param form: A WTForms `Form` instance
    :param fields: A list of fields to be displayed on the form
    :param submit: The title of the submit button
    :param back: The title of the back button
    :param back_url: The URL the back button redirects to
    :param back_button: Whether to show a back button
    :param disabled_until_change: Whether to disable form submission
                                  until a field is changed
    :param disabled_fields: List of field names to disable
    :param form_header_kwargs: Keyword arguments passed to the
                               ``form_header`` macro
    :param skip_labels: Whether to show labels on the fields
    :param save_reminder: Whether to show a message when the form has
                          been modified and the save button is not
                          visible
    :param footer_align_right: Whether the buttons in the event footer
                               should be aligned to the right.
    :param disable_if_locked: Whether the form should be disabled when
                              the associated event is locked (based on
                              a CSS class in the DOM structure)
    """
    if submit is None:
        submit = _('Save')
    if back is None:
        back = _('Cancel')
    if form_header_kwargs is None:
        form_header_kwargs = {}
    tpl = get_template_module('forms/_form.html')
    html = tpl.simple_form(form, fields=fields, submit=submit, back=back, back_url=back_url, back_button=back_button,
                           disabled_until_change=disabled_until_change, disabled_fields=disabled_fields,
                           form_header_kwargs=form_header_kwargs, skip_labels=skip_labels, save_reminder=save_reminder,
                           footer_align_right=footer_align_right, disable_if_locked=disable_if_locked, message=message)
    return jsonify(html=html, js=_pop_injected_js())


def jsonify_template(template, _render_func=render_template, _success=None, **context):
    """Return a json response containing a rendered template."""
    html = _render_func(template, **context)
    jsonify_kw = {}
    if _success is not None:
        jsonify_kw['success'] = _success
    return jsonify(html=html, js=_pop_injected_js(), **jsonify_kw)


def jsonify_data(flash=True, **json_data):
    """Return a json response with some default fields.

    This behaves similar to :func:`~flask.jsonify`, but includes
    ``success=True`` and flashed messages by default.

    :param flash: if the json data should contain flashed messages
    :param json_data: the data to include in the json response
    """
    json_data.setdefault('success', True)
    if flash:
        json_data['flashed_messages'] = render_template('flashed_messages.html')
    return jsonify(**json_data)


class ExpectedError(ImATeapot):
    """
    An error that is expected to happen and is guaranteed to be handled
    by client-side code.

    Use this class in new react-based code together with the AJAX
    actions when you expect things to go wrong and want to handle
    them in a nicer way than the usual error dialog.

    :param message: A short message describing the error
    :param data: Any additional data to return
    """
    def __init__(self, message, **data):
        super(ExpectedError, self).__init__(message or 'Something went wrong')
        self.data = dict(data, message=message)


def _format_request_data(data, hide_passwords=False):
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
    """Get various information about the current HTTP request.

    This is especially useful for logging purposes where you want
    as many information as possible.

    :param hide_passwords: Hides the actual value of POST fields
                           if their name contains ``password``.

    :return: a dictionary containing request information, or ``None``
             when called outside a request context
    """
    if not has_request_context():
        return None
    try:
        user_info = {
            'id': session.user.id,
            'name': session.user.full_name,
            'email': session.user.email
        } if session.user else None
    except Exception as exc:
        user_info = 'ERROR: {}'.format(exc)
    return {
        'id': request.id,
        'time': datetime.now().isoformat(),
        'url': request.url,
        'endpoint': request.url_rule.endpoint if request.url_rule else None,
        'method': request.method,
        'rh': g.rh.__class__.__name__ if 'rh' in g else None,
        'user': user_info,
        'ip': request.remote_addr,
        'user_agent': unicode(request.user_agent),
        'referrer': request.referrer,
        'data': {
            'url': _format_request_data(request.view_args) if request.view_args is not None else None,
            'get': _format_request_data(request.args),
            'post': _format_request_data(request.form, hide_passwords=hide_passwords),
            'json': request.get_json(silent=True),
            'headers': _format_request_data(request.headers, False),
        }
    }


def url_for_index(_external=False, _anchor=None):
    from indico.web.flask.util import url_for
    return url_for('categories.display', _external=_external, _anchor=_anchor)


def signed_url_for(user, blueprint, url_params=None, *args, **kwargs):
    """Get a URL from a blueprint, which is signed using a user's signing secret."""
    from indico.web.flask.util import url_for
    _external = kwargs.pop('_external', False)
    base_url = url_for(blueprint, *args, **(url_params or {}))
    qs = url_encode(sorted(kwargs.items()))
    # this is the URL which is to be signed
    url = '{}?{}'.format(base_url, qs) if qs else base_url

    signer = Signer(user.signing_secret, salt='url-signing')
    qs = url_encode(dict(kwargs, token=signer.get_signature(url)))
    full_base_url = url_for(blueprint, *args, _external=_external, **(url_params or {}))

    # this is the final URL including the signature ('token' parameter)
    return '{}?{}'.format(full_base_url, qs) if qs else base_url


def is_signed_url_valid(user, url):
    """Check whether a signed URL is valid according to the user's signing secret."""
    parsed = url_parse(url)
    params = url_decode(parsed.query)
    try:
        signature = params.pop('token')
    except KeyError:
        return False

    url = url_unparse((
        '',
        '',
        parsed.path,
        url_encode(sorted(params.items()), sort=True),
        parsed.fragment
    ))
    signer = Signer(user.signing_secret, salt='url-signing')
    return signer.verify_signature(url, signature)
