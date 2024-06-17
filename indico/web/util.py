# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import hashlib
import sys
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import sentry_sdk
from authlib.oauth2 import OAuth2Error
from flask import flash, g, has_request_context, jsonify, render_template, request, session
from itsdangerous import Signer
from markupsafe import Markup
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest, Forbidden, ImATeapot, RequestEntityTooLarge

from indico.util.caching import memoize_request
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
        super().__init__(message or 'Something went wrong')
        self.data = dict(data, message=message)


def _format_request_data(data, hide_passwords=False):
    if not hasattr(data, 'lists'):
        data = ((k, [v]) for k, v in data.items())
    else:
        data = data.lists()
    rv = {}
    for key, values in data:
        if hide_passwords and 'password' in key:
            values = [v if not v else f'<{len(v)} chars hidden>' for v in values]
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
        user_info = f'ERROR: {exc}'
    try:
        request_data = {
            'get': _format_request_data(request.args),
            'post': _format_request_data(request.form, hide_passwords=hide_passwords),
            'json': request.get_json(silent=True),
        }
    except RequestEntityTooLarge as exc:
        request_data = {'ERROR': str(exc)}
    return {
        'id': request.id,
        'time': datetime.now().isoformat(),
        'url': request.url,
        'endpoint': request.url_rule.endpoint if request.url_rule else None,
        'method': request.method,
        'rh': g.rh.__class__.__name__ if 'rh' in g else None,
        'user': user_info,
        'ip': request.remote_addr,
        'user_agent': str(request.user_agent),
        'referrer': request.referrer,
        'data': {
            'url': _format_request_data(request.view_args) if request.view_args is not None else None,
            **request_data,
            'headers': _format_request_data(request.headers, False),
        }
    }


def url_for_index(_external=False, _anchor=None):
    from indico.web.flask.util import url_for
    return url_for('categories.display', _external=_external, _anchor=_anchor)


def is_legacy_signed_url_valid(user, url):
    """Check whether a legacy signed URL is valid for a user.

    This util is deprecated and only exists because people may be actively
    using URLs using the old style token. Any new code should use the new
    :func:`signed_url_for_user` and :func:`verify_signed_user_url` utils
    which encode the user id within the signature.
    """
    parsed = urlsplit(url)
    params = MultiDict(parse_qs(parsed.query))
    try:
        signature = params.pop('token')
    except KeyError:
        return False

    url = urlunsplit((
        '',
        '',
        parsed.path,
        urlencode(list(params.lists()), doseq=True),
        parsed.fragment
    ))
    signer = Signer(user.signing_secret, salt='url-signing')
    return signer.verify_signature(url.encode(), signature)


def _get_user_url_signer(user):
    return Signer(user.signing_secret, salt='user-url-signing', digest_method=hashlib.sha256)


def signed_url_for_user(user, endpoint, /, *args, **kwargs):
    """Get a URL for an endpoint, which is signed using a user's signing secret.

    The user id, path and query string are encoded within the signature.
    """
    from indico.web.flask.util import url_for

    _external = kwargs.pop('_external', False)
    url = url_for(endpoint, *args, **kwargs)

    # we include the plain userid in the token so we know which signing secret to load.
    # the signature itself is over the method, user id and URL, so tampering with that ID
    # would not help.
    # using signed urls for anything that's not GET is also very unlikely, but we include
    # the method as well just to make sure we don't accidentally sign some URL where POST
    # is more powerful and has a body that's not covered by the signature. if we ever want
    # to allow such a thing we could of course make the method configurable instead of
    # hardcoding GET.
    signer = _get_user_url_signer(user)
    signature_data = f'GET:{user.id}:{url}'
    signature = signer.get_signature(signature_data).decode()
    user_token = f'{user.id}_{signature}'

    # this is the final URL including the signature ('user_token' parameter); it also
    # takes the `_external` flag into account (which is omitted for the signature in
    # order to never include the host in the signed part)
    return url_for(endpoint, *args, **kwargs, _external=_external, user_token=user_token)


def verify_signed_user_url(url, method):
    """Verify a signed URL and extract the associated user.

    :param url: the full relative URL of the request, including the query string
    :param method: the HTTP method of the request

    :return: the user associated with the signed link or `None` if no token was provided
    :raise Forbidden: if a token is present but invalid
    """
    from indico.modules.users import User
    parsed = urlsplit(url)
    params = MultiDict(parse_qs(parsed.query))
    try:
        user_id, signature = params.pop('user_token').split('_', 1)
        user_id = int(user_id)
    except KeyError:
        return None
    except ValueError:
        raise BadRequest(_('The persistent link you used is invalid.'))

    url = urlunsplit((
        '',
        '',
        parsed.path,
        urlencode(list(params.lists()), doseq=True),
        parsed.fragment
    ))

    user = User.get(user_id)
    if not user:
        raise BadRequest(_('The persistent link you used is invalid.'))

    signer = _get_user_url_signer(user)
    signature_data = f'{method}:{user.id}:{url}'
    if not signer.verify_signature(signature_data.encode(), signature):
        raise BadRequest(_('The persistent link you used is invalid.'))

    return user


def get_oauth_user(scopes):
    from indico.core.oauth import require_oauth
    from indico.core.oauth.util import TOKEN_PREFIX_SERVICE
    token = request.headers.get('Authorization', '')
    if not token.lower().startswith('bearer ') or token.lower().startswith(f'bearer {TOKEN_PREFIX_SERVICE}'):
        return None
    try:
        oauth_token = require_oauth.acquire_token(scopes)
    except OAuth2Error as exc:
        require_oauth.raise_error_response(exc)
    return oauth_token.user


def _lookup_request_user(allow_signed_url=False, oauth_scope_hint=None):
    oauth_scopes = [oauth_scope_hint] if oauth_scope_hint else []
    if request.method == 'GET':
        oauth_scopes += ['read:everything', 'full:everything']
    else:
        oauth_scopes += ['full:everything']

    signed_url_user = verify_signed_user_url(request.full_path, request.method)
    oauth_user = get_oauth_user(oauth_scopes)
    session_user = session.get_session_user()

    if oauth_user:
        if signed_url_user:
            raise BadRequest('OAuth tokens and signed URLs cannot be mixed')
        if session_user:
            raise BadRequest('OAuth tokens and session cookies cannot be mixed')

    if signed_url_user and not allow_signed_url:
        raise BadRequest('Signature auth is not allowed for this URL')

    if signed_url_user:
        return signed_url_user, 'signed_url'
    elif oauth_user:
        return oauth_user, 'oauth'
    elif session_user:
        return session_user, 'session'

    return None, None


def _request_likely_seen_by_user():
    return not request.is_xhr and not request.is_json and request.blueprint != 'assets'


def _check_request_user(user, source):
    if not user:
        return None, None
    elif user.is_deleted:
        merged_into_user = user.merged_into_user
        if source != 'session':
            if merged_into_user:
                raise Forbidden('User has been merged into another user')
            else:
                raise Forbidden('User has been deleted')
        user = source = None
        # If the user is deleted and the request is likely to be seen by
        # the user, we forcefully log him out and inform him about it.
        if _request_likely_seen_by_user():
            session.clear()
            if merged_into_user:
                msg = _('Your profile has been merged into <strong>{}</strong>. Please log in using that profile.')
                flash(Markup(msg).format(merged_into_user.full_name), 'warning')
            else:
                flash(_('Your profile has been deleted.'), 'error')
    elif user.is_blocked:
        if source != 'session':
            raise Forbidden('User has been blocked')
        user = source = None
        if _request_likely_seen_by_user():
            session.clear()
            flash(_('Your profile has been blocked.'), 'error')

    return user, source


@memoize_request
def get_request_user():
    """Get the user associated with the current request.

    This looks up the user using all ways of authentication that are
    supported on the current endpoint. In most cases that's the user
    from the active session (via a session cookie), but it may also be
    set (or even overridden if there is a session as well) through other
    means, such as:

    - an OAuth token
    - a signature for a persistent url
    """
    if g.get('get_request_user_failed'):
        # If getting the current user failed, we abort early in case something
        # tries again since that code may be in logging or error handling, and
        # we don't want that code to fail because of an invalid token in the URL
        return None, None

    # XXX this is an awful workaround for API requests than call something (e.g.
    # `display_full_name`) which accesses `session.user` and thus calls this,
    # which will then fail because the API token usually doesn't have one of the
    # `everything` scopes... this should be removed whenever we get rid of the legacy
    # API since any new code would simply be using normal RHs with an oauth scope,
    # and thus not end up doing this weird mix.
    if g.get('current_api_user'):
        return None, None

    current_exc = sys.exc_info()[1]
    rh = type(g.rh) if 'rh' in g else None

    if getattr(rh, '_DISABLE_CORE_AUTH', False):
        return None, None

    oauth_scope_hint = getattr(rh, '_OAUTH_SCOPE', None)
    allow_signed_url = getattr(rh, '_ALLOW_SIGNED_URL', False)

    try:
        user, source = _lookup_request_user(allow_signed_url, oauth_scope_hint)
        user, source = _check_request_user(user, source)
    except Exception as exc:
        g.get_request_user_failed = True
        if current_exc:
            # If we got here while handling another exception, we silently ignore
            # any failure related to authenticating the current user and pretend
            # there is no user so we can continue handling the original exception.
            # one case when this happens is passing a `user_token` arg to a page
            # that 404s. of course the token is not valid there, but the 404 error
            # is the more interesting one.
            from indico.core.logger import Logger
            Logger.get('auth').info('Discarding exception "%s" while authenticating request user during handling of '
                                    'exception "%s"', exc, current_exc)
            return None, None
        raise

    if user:
        sentry_sdk.set_user({
            'id': user.id,
            'email': user.email,
            'name': user.full_name,
            'source': source
        })

    return user, source


def strip_path_from_url(url):
    """Strip away the path from a given URL.

    (e.g. https://foo.bar/baz?qux -> https://foo.bar)
    """
    url = urlsplit(url, allow_fragments=False)

    if not url.netloc:
        # return the original URL if it's not a valid URL
        return url.geturl()

    return urlunsplit(url._replace(path='', query=''))
