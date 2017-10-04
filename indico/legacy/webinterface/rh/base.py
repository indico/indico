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

import cProfile
import inspect
import itertools
import os
import pstats
import random
from functools import partial, wraps

import jsonschema
from flask import current_app, g, redirect, request, session
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest, Forbidden, MethodNotAllowed, NotFound
from werkzeug.routing import BuildError
from werkzeug.wrappers import Response

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.core import handle_sqlalchemy_database_error
from indico.core.errors import NoReportError
from indico.core.logger import Logger, sentry_set_tags
from indico.legacy.common import fossilize
from indico.legacy.common.mail import GenericMailer
from indico.legacy.common.security import Sanitization
from indico.legacy.errors import NotLoggedError
from indico.legacy.webinterface.pages.errors import WPKeyAccessError
from indico.modules.events.legacy import LegacyConference
from indico.util.i18n import _
from indico.util.locators import get_locator
from indico.web.flask.util import ResponseUtil, create_flat_args, url_for


HTTP_VERBS = {'GET', 'PATCH', 'POST', 'PUT', 'DELETE'}

logger = Logger.get('rh')


class RequestHandlerBase(object):
    def _process_args(self):
        """
        This method is called before _check_access and url normalization
        and is a good place to fetch objects from the database based on
        variables from request params.
        """

    def _check_access(self):
        """
        This method is called after _process_args and is a good place
        to check if the user is permitted to perform some actions.
        """


class RH(RequestHandlerBase):
    NOT_SANITIZED_FIELDS = frozenset()
    CSRF_ENABLED = True  # require a csrf_token when accessing the RH with anything but GET
    EVENT_FEATURE = None  # require a certain event feature when accessing the RH. See `EventFeature` for details
    DENY_FRAMES = False  # whether to send an X-Frame-Options:DENY header

    #: A dict specifying how the url should be normalized.
    #: `args` is a dictionary mapping view args keys to callables
    #: used to retrieve the expected value for those arguments if they
    #: are present in the request's view args.
    #: `locators` is a set of callables returning objects with locators.
    #: `preserved_args` is a set of view arg names which will always
    #: be copied from the current request if present.
    #: The callables are always invoked with a single `self` argument
    #: containing the RH instance.
    #: `endpoint` may be used to specify the endpoint used to build
    #: the URL in case of a redirect.  Usually this should not be used
    #: in favor of ``request.endpoint`` being used if no custom endpoint
    #: is set.
    #: Arguments specified in the `defaults` of any rule matching the
    #: current endpoint are always excluded when checking if the args
    #: match or when building a new URL.
    #: If the view args built from the returned objects do not match
    #: the request's view args, a redirect is issued automatically.
    #: If the request is not using GET/HEAD, a 404 error is raised
    #: instead of a redirect since such requests cannot be redirected
    #: but executing them on the wrong URL may pose a security risk in
    #: case and of the non-relevant URL segments is used for access
    #: checks.
    normalize_url_spec = {
        'args': {},
        'locators': set(),
        'preserved_args': set(),
        'endpoint': None
    }

    def __init__(self):
        self.commit = True
        self._responseUtil = ResponseUtil()
        self._target = None
        self._endTime = None

    # Methods =============================================================

    def validate_json(self, schema, json=None):
        """Validates the request's JSON payload using a JSON schema.

        :param schema: The JSON schema used for validation.
        :param json: The JSON object (defaults to ``request.json``)
        :raises BadRequest: if the JSON validation failed
        """
        if json is None:
            json = request.json
        try:
            jsonschema.validate(json, schema)
        except jsonschema.ValidationError as e:
            raise BadRequest('Invalid JSON payload: {}'.format(e.message))

    @property
    def csrf_token(self):
        return session.csrf_token if session.csrf_protected else ''

    def normalize_url(self):
        """Performs URL normalization.

        This uses the :attr:`normalize_url_spec` to check if the URL
        params are what they should be and redirects or fails depending
        on the HTTP method used if it's not the case.

        :return: ``None`` or a redirect response
        """
        if current_app.debug and self.normalize_url_spec is RH.normalize_url_spec:
            # in case of ``class SomeRH(RH, MixinWithNormalization)``
            # the default value from `RH` overwrites the normalization
            # rule from ``MixinWithNormalization``.  this is never what
            # the developer wants so we fail if it happens.  the proper
            # solution is ``class SomeRH(MixinWithNormalization, RH)``
            cls = next((x
                        for x in inspect.getmro(self.__class__)
                        if (x is not RH and x is not self.__class__ and hasattr(x, 'normalize_url_spec') and
                            getattr(x, 'normalize_url_spec', None) is not RH.normalize_url_spec)),
                       None)
            if cls is not None:
                raise Exception('Normalization rule of {} in {} is overwritten by base RH. Put mixins with class-level '
                                'attributes on the left of the base class'.format(cls, self.__class__))
        if not self.normalize_url_spec or not any(self.normalize_url_spec.itervalues()):
            return
        spec = {
            'args': self.normalize_url_spec.get('args', {}),
            'locators': self.normalize_url_spec.get('locators', set()),
            'preserved_args': self.normalize_url_spec.get('preserved_args', set()),
            'endpoint': self.normalize_url_spec.get('endpoint', None)
        }
        # Initialize the new view args with preserved arguments (since those would be lost otherwise)
        new_view_args = {k: v for k, v in request.view_args.iteritems() if k in spec['preserved_args']}
        # Retrieve the expected values for all simple arguments (if they are currently present)
        for key, getter in spec['args'].iteritems():
            if key in request.view_args:
                new_view_args[key] = getter(self)
        # Retrieve the expected values from locators
        prev_locator_args = {}
        for getter in spec['locators']:
            value = getter(self)
            if value is None:
                raise NotFound('The URL contains invalid data. Please go to the previous page and refresh it.')
            locator_args = get_locator(value)
            reused_keys = set(locator_args) & prev_locator_args.viewkeys()
            if any(locator_args[k] != prev_locator_args[k] for k in reused_keys):
                raise NotFound('The URL contains invalid data. Please go to the previous page and refresh it.')
            new_view_args.update(locator_args)
            prev_locator_args.update(locator_args)
        # Get all default values provided by the url map for the endpoint
        defaults = set(itertools.chain.from_iterable(r.defaults
                                                     for r in current_app.url_map.iter_rules(request.endpoint)
                                                     if r.defaults))

        def _convert(v):
            # some legacy code has numeric ids in the locator data, but still takes
            # string ids in the url rule (usually for confId)
            return unicode(v) if isinstance(v, (int, long)) else v

        provided = {k: _convert(v) for k, v in request.view_args.iteritems() if k not in defaults}
        new_view_args = {k: _convert(v) for k, v in new_view_args.iteritems()}
        if new_view_args != provided:
            if request.method in {'GET', 'HEAD'}:
                endpoint = spec['endpoint'] or request.endpoint
                try:
                    return redirect(url_for(endpoint, **dict(request.args.to_dict(), **new_view_args)))
                except BuildError as e:
                    if current_app.debug:
                        raise
                    logger.warn('BuildError during normalization: %s', e)
                    raise NotFound
            else:
                raise NotFound('The URL contains invalid data. Please go to the previous page and refresh it.')

    def _process(self):
        """The default process method dispatches to a method containing
        the HTTP verb used for the current request, e.g. _process_POST.
        When implementing this please consider that you most likely want/need
        only GET and POST - the other verbs are not supported everywhere!
        """
        method = getattr(self, '_process_' + request.method, None)
        if method is None:
            valid_methods = [m for m in HTTP_VERBS if hasattr(self, '_process_' + m)]
            raise MethodNotAllowed(valid_methods)
        return method()

    def _check_csrf(self):
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if token is None:
            # Might be a WTForm with a prefix. In that case the field name is '<prefix>-csrf_token'
            token = next((v for k, v in request.form.iteritems() if k.endswith('-csrf_token')), None)
        if self.CSRF_ENABLED and request.method != 'GET' and token != session.csrf_token:
            msg = _(u"It looks like there was a problem with your current session. Please use your browser's back "
                    u"button, reload the page and try again.")
            raise BadRequest(msg)

    def _check_event_feature(self):
        from indico.modules.events.features.util import require_feature
        event_id = request.view_args.get('confId') or request.view_args.get('event_id')
        if event_id is not None:
            require_feature(event_id, self.EVENT_FEATURE)

    def _check_auth(self):
        if session.user:
            logger.info('Request authenticated: %r', session.user)
        self._check_csrf()

    def _do_process(self, profile):
        try:
            args_result = self._process_args()
            if isinstance(args_result, (current_app.response_class, Response)):
                return '', args_result
        except NoResultFound:  # sqlalchemy .one() not finding anything
            raise NotFound(_(u'The specified item could not be found.'))

        rv = self.normalize_url()
        if rv is not None:
            return '', rv

        try:
            self._check_access()
        except AccessKeyRequired:
            return '', WPKeyAccessError(self).display()
        Sanitization.sanitizationCheck(create_flat_args(), self.NOT_SANITIZED_FIELDS)

        if profile:
            profile_name = os.path.join(config.TEMP_DIR, 'stone{}.prof'.format(random.random()))
            result = [None]
            cProfile.runctx('result[0] = self._process()', globals(), locals(), profile_name)
            return profile_name, result[0]
        else:
            return '', self._process()

    def process(self):
        if request.method not in HTTP_VERBS:
            # Just to be sure that we don't get some crappy http verb we don't expect
            raise BadRequest

        profile = config.PROFILE
        profile_name, res = '', ''

        g.rh = self
        sentry_set_tags({'rh': self.__class__.__name__})

        if self.EVENT_FEATURE is not None:
            self._check_event_feature()

        logger.info(u'Request started: %s %s [IP=%s] [PID=%s]',
                    request.method, request.relative_url, request.remote_addr, os.getpid())

        try:
            fossilize.clearCache()
            GenericMailer.flushQueue(False)
            self._check_auth()
            profile_name, res = self._do_process(profile)
            signals.after_process.send()

            if self.commit:
                if GenericMailer.has_queue():
                    # ensure we fail early (before sending out e-mails)
                    # in case there are DB constraint violations, etc...
                    db.enforce_constraints()
                    GenericMailer.flushQueue(True)

                db.session.commit()
            else:
                db.session.rollback()
        except DatabaseError:
            handle_sqlalchemy_database_error()  # this will re-raise an exception
        logger.debug('Request successful')

        # log request timing
        if profile and os.path.isfile(profile_name):
            rep = config.TEMP_DIR
            stats = pstats.Stats(profile_name)
            stats.sort_stats('cumulative', 'time', 'calls')
            stats.dump_stats(os.path.join(rep, 'IndicoRequestProfile.log'))
            os.remove(profile_name)

        if res is None:
            return self._responseUtil.make_empty()

        response = self._responseUtil.make_response(res)
        if self.DENY_FRAMES:
            response.headers['X-Frame-Options'] = 'DENY'
        return response


class RHSimple(RH):
    """A simple RH that calls a function to build the response

    The preferred way to use this class is by using the
    `RHSimple.wrap_function` decorator.

    :param func: A function returning HTML
    """
    def __init__(self, func):
        RH.__init__(self)
        self.func = func

    def _process(self):
        rv = self.func()
        return rv

    @classmethod
    def wrap_function(cls, func):
        """Decorates a function to run within the RH's framework"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cls(partial(func, *args, **kwargs)).process()

        return wrapper


class RHProtected(RH):
    def _checkSessionUser(self):
        if session.user is None:
            if 'application/json' in request.headers.get('Content-Type', 'text/html'):
                raise NotLoggedError("You are currently not authenticated. Please log in again.")
            else:
                raise Forbidden

    def _check_access(self):
        self._checkSessionUser()


class AccessKeyRequired(Forbidden):
    pass


class RHDisplayBaseProtected(RHProtected):
    def _check_access(self):
        if not isinstance(self._target, LegacyConference):
            raise Exception('Unexpected object')
        event = self._target.as_event
        can_access = event.can_access(session.user)
        if not can_access and event.access_key:
            raise AccessKeyRequired
        if can_access:
            return
        elif session.user is None:
            self._checkSessionUser()
        else:
            msg = [_(u"You are not authorized to access this event.")]
            if event.no_access_contact:
                msg.append(_(u"If you believe you should have access, please contact {}")
                           .format(event.no_access_contact))
            raise Forbidden(u' '.join(msg))


class RHModificationBaseProtected(RHProtected):
    ALLOW_LOCKED = False
    ROLE = None

    def _check_access(self):
        if not isinstance(self._target, LegacyConference):
            raise Exception('Unexpected object')
        event = self._target.as_event
        if not event.can_manage(session.user, role=self.ROLE):
            if session.user is None:
                self._checkSessionUser()
            else:
                raise Forbidden(_(u'You are not authorized to manage this event.'))
        check_event_locked(self, event)


def check_event_locked(rh, event, force=False):
    if (not getattr(rh, 'ALLOW_LOCKED', False) or force) and event.is_locked and request.method not in ('GET', 'HEAD'):
        raise NoReportError.wrap_exc(Forbidden(_(u'This event has been locked so no modifications are possible.')))
