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
import copy
import inspect
import itertools
import os
import pstats
import random
from datetime import datetime
from functools import wraps, partial
from xml.sax.saxutils import escape

import jsonschema
from flask import request, session, g, current_app, redirect
from itsdangerous import BadData
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest, MethodNotAllowed, NotFound, Forbidden, HTTPException
from werkzeug.routing import BuildError
from werkzeug.wrappers import Response

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.core.db.sqlalchemy.core import handle_sqlalchemy_database_error
from indico.core.errors import get_error_description, NoReportError
from indico.core.logger import Logger
from indico.legacy.accessControl import AccessWrapper
from indico.legacy.common import fossilize
from indico.legacy.common.mail import GenericMailer
from indico.legacy.common.security import Sanitization
from indico.legacy.errors import (AccessError, BadRefererError, KeyAccessError, MaKaCError, ModificationError,
                                  NotLoggedError, NotFoundError)
from indico.legacy.webinterface.pages.error import render_error
from indico.legacy.webinterface.pages.errors import (WPGenericError, WPUnexpectedError, WPAccessError, WPKeyAccessError,
                                                     WPModificationError, WPFormValuesError, WPNoReportError,
                                                     WPRestrictedHTML)
from indico.modules.auth.util import url_for_login, redirect_to_login
from indico.modules.events.legacy import LegacyConference
from indico.util.decorators import jsonify_error
from indico.util.i18n import _
from indico.util.locators import get_locator
from indico.util.string import truncate
from indico.web.flask.util import ResponseUtil, url_for


HTTP_VERBS = {'GET', 'PATCH', 'POST', 'PUT', 'DELETE'}

logger = Logger.get('requestHandler')


class RequestHandlerBase(object):

    def _checkProtection(self):
        """This method is called after _checkParams and is a good place
        to check if the user is permitted to perform some actions.

        If you only want to run some code for GET or POST requests, you can create
        a method named e.g. _checkProtection_POST which will be executed AFTER this one.
        """
        pass

    def getAW(self):
        """
        Returns the access wrapper related to this session/user
        """
        return self._aw

    accessWrapper = property(getAW)

    def _getUser(self):
        """
        Returns the current user
        """
        return self._aw.getUser()

    def _setUser(self, new_user=None):
        """
        Sets the current user
        """
        self._aw.setUser(new_user)

    def getRequestParams(self):
        return self._params

    def _getTruncatedParams(self):
        """Truncates params"""
        params = {}
        for key, value in self._reqParams.iteritems():
            if key in {'password', 'confirm_password'}:
                params[key] = '[password hidden, len=%d]' % len(value)
            elif isinstance(value, basestring):
                params[key] = truncate(value, 1024)
            else:
                params[key] = value
        return params


class RH(RequestHandlerBase):
    _doNotSanitizeFields = []
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
        self._aw = AccessWrapper()  # Fill in the aw instance with the current information
        self._target = None
        self._reqParams = {}
        self._startTime = None
        self._endTime = None
        self._doProcess = True

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

    def _setSessionUser(self):
        self._aw.setUser(session.avatar)

    @property
    def csrf_token(self):
        return session.csrf_token if session.csrf_protected else ''

    def getRequestParams(self):
        return self._reqParams

    def _redirect(self, targetURL, status=303):
        if isinstance(targetURL, Response):
            status = targetURL.status_code
            targetURL = targetURL.headers['Location']
        else:
            targetURL = str(targetURL)
        if "\r" in targetURL or "\n" in targetURL:
            raise MaKaCError(_("http header CRLF injection detected"))
        self._responseUtil.redirect = (targetURL, status)

    def _processError(self, e):
        raise

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

    def _checkParams(self, params):
        """This method is called before _checkProtection and is a good place
        to assign variables from request params to member variables.

        Note that in any new code the params argument SHOULD be IGNORED.
        Use the following objects provided by Flask instead:
        from flask import request
        request.view_args (URL route params)
        request.args (GET params (from the query string))
        request.form (POST params)
        request.values (GET+POST params - use only if ABSOLUTELY NECESSARY)

        If you only want to run some code for GET or POST requests, you can create
        a method named e.g. _checkParams_POST which will be executed AFTER this one.
        The method is called without any arguments (except self).
        """
        pass

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

    def _checkCSRF(self):
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if token is None:
            # Might be a WTForm with a prefix. In that case the field name is '<prefix>-csrf_token'
            token = next((v for k, v in request.form.iteritems() if k.endswith('-csrf_token')), None)
        if self.CSRF_ENABLED and request.method != 'GET' and token != session.csrf_token:
            msg = _(u"It looks like there was a problem with your current session. Please use your browser's back "
                    u"button, reload the page and try again.")
            raise BadRequest(msg)
        # legacy csrf check (referer-based):
        # Check referer for POST requests. We do it here so we can properly use indico's error handling
        if Config.getInstance().getCSRFLevel() < 3 or request.method != 'POST':
            return
        referer = request.referrer
        # allow empty - otherwise we might lock out paranoid users blocking referers
        if not referer:
            return
        # valid http referer
        if referer.startswith(Config.getInstance().getBaseURL()):
            return
        raise BadRefererError('This operation is not allowed from an external referer.')

    def _check_event_feature(self):
        from indico.modules.events.features.util import require_feature
        event_id = request.view_args.get('confId') or request.view_args.get('event_id')
        if event_id is not None:
            require_feature(event_id, self.EVENT_FEATURE)

    @jsonify_error
    def _processGeneralError(self, e):
        """Treats general errors occured during the process of a RH."""

        if Config.getInstance().getPropagateAllExceptions():
            raise
        return WPGenericError(self).display()

    @jsonify_error(status=500, logging_level='exception')
    def _processUnexpectedError(self, e):
        """Unexpected errors"""

        self._responseUtil.redirect = None
        if Config.getInstance().getEmbeddedWebserver() or Config.getInstance().getPropagateAllExceptions():
            raise
        return WPUnexpectedError(self).display()

    @jsonify_error(status=403)
    def _processForbidden(self, e):
        if session.user is None and not request.is_xhr and not e.response and request.blueprint != 'auth':
            return redirect_to_login(reason=_("Please log in to access this page."))
        message = _("Access Denied")
        explanation = get_error_description(e)
        return render_error(message, explanation)

    @jsonify_error(status=400)
    def _processBadRequest(self, e):
        message = _("Bad Request")
        return render_error(message, e.description)

    @jsonify_error(status=401)
    def _processUnauthorized(self, e):
        message = _("Unauthorized")
        return render_error(message, e.description)

    @jsonify_error(status=400)
    def _processBadData(self, e):
        message = _("Invalid or expired token")
        return render_error(message, e.message)

    @jsonify_error(status=403)
    def _processAccessError(self, e):
        """Treats access errors occured during the process of a RH."""
        return WPAccessError(self).display()

    @jsonify_error
    def _processKeyAccessError(self, e):
        """Treats access errors occured during the process of a RH."""
        return WPKeyAccessError(self).display()

    @jsonify_error
    def _processModificationError(self, e):
        """Handles modification errors occured during the process of a RH."""
        if not session.user:
            return redirect_to_login(reason=_("Please log in to access this page. If you have a modification key, you "
                                              "may enter it afterwards."))
        return WPModificationError(self).display()

    @jsonify_error(status=400)
    def _processBadRequestKeyError(self, e):
        """Request lacks a necessary key for processing"""
        msg = _('Required argument missing: %s') % e.message
        return WPFormValuesError(self, msg).display()

    @jsonify_error
    def _processNoReportError(self, e):
        """Process errors without reporting"""
        return WPNoReportError(self, e).display()

    @jsonify_error(status=400)
    def _processUserValueError(self, e):
        """Process errors without reporting"""
        return WPNoReportError(self, e).display()

    @jsonify_error(status=404)
    def _processNotFoundError(self, e):
        if isinstance(e, NotFound):
            message = _("Page not found")  # that's a bit nicer than "404: Not Found"
            explanation = get_error_description(e)
        else:
            message = e.getMessage()
            explanation = e.getExplanation()
        return render_error(message, explanation)

    @jsonify_error
    def _processFormValuesError(self, e):
        """Treats user input related errors occured during the process of a RH."""

        return WPFormValuesError(self, e).display()

    @jsonify_error
    def _processRestrictedHTML(self, e):
        return WPRestrictedHTML(self, escape(str(e))).display()

    @jsonify_error
    def _processHtmlForbiddenTag(self, e):
        return WPRestrictedHTML(self, escape(str(e))).display()

    def _check_auth(self, params):
        self._setSessionUser()
        if session.user:
            logger.info('Request authenticated: %r', session.user)
        self._checkCSRF()
        self._reqParams = copy.copy(params)

    def _do_process(self, profile):
        profile_name = res = ''
        try:
            # old code gets parameters from call
            # new code utilizes of flask.request
            if len(inspect.getargspec(self._checkParams).args) < 2:
                cp_result = self._checkParams()
            else:
                cp_result = self._checkParams(self._reqParams)

            if isinstance(cp_result, (current_app.response_class, Response)):
                return '', cp_result

            func = getattr(self, '_checkParams_' + request.method, None)
            if func:
                cp_result = func()
                if isinstance(cp_result, (current_app.response_class, Response)):
                    return '', cp_result

        except NoResultFound:  # sqlalchemy .one() not finding anything
            raise NotFoundError(_('The specified item could not be found.'), title=_('Item not found'))

        rv = self.normalize_url()
        if rv is not None:
            return '', rv

        self._checkProtection()
        func = getattr(self, '_checkProtection_' + request.method, None)
        if func:
            func()

        Sanitization.sanitizationCheck(self._target, self._reqParams, self._aw, self._doNotSanitizeFields)

        if self._doProcess:
            if profile:
                profile_name = os.path.join(Config.getInstance().getTempDir(), 'stone{}.prof'.format(random.random()))
                result = [None]
                cProfile.runctx('result[0] = self._process()', globals(), locals(), profile_name)
                res = result[0]
            else:
                res = self._process()
        return profile_name, res

    def process(self, params):
        if request.method not in HTTP_VERBS:
            # Just to be sure that we don't get some crappy http verb we don't expect
            raise BadRequest

        cfg = Config.getInstance()
        profile = cfg.getProfile()
        profile_name, res, textLog = '', '', []

        self._startTime = datetime.now()

        g.rh = self

        if self.EVENT_FEATURE is not None:
            self._check_event_feature()

        textLog.append("%s : Database request started" % (datetime.now() - self._startTime))
        logger.info(u'Request started: %s %s [IP=%s] [PID=%s]',
                    request.method, request.relative_url, request.remote_addr, os.getpid())

        is_error_response = False
        try:
            try:
                fossilize.clearCache()
                GenericMailer.flushQueue(False)
                self._check_auth(params)
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
            logger.info('Request successful')
        except Exception as e:
            db.session.rollback()
            res = self._getMethodByExceptionName(e)(e)
            if isinstance(e, HTTPException) and e.response is not None:
                res = e.response
            is_error_response = True

        totalTime = (datetime.now() - self._startTime)
        textLog.append('{} : Request ended'.format(totalTime))

        # log request timing
        if profile and os.path.isfile(profile_name):
            rep = Config.getInstance().getTempDir()
            stats = pstats.Stats(profile_name)
            stats.sort_stats('cumulative', 'time', 'calls')
            stats.dump_stats(os.path.join(rep, 'IndicoRequestProfile.log'))
            os.remove(profile_name)

        if is_error_response and isinstance(res, (current_app.response_class, Response)):
            # if we went through error handling code, responseUtil._status has been changed
            # so make_response() would fail
            return res

        # In case of no process needed, we should return empty string to avoid erroneous output
        # specially with getVars breaking the JS files.
        if not self._doProcess or res is None:
            return self._responseUtil.make_empty()

        response = self._responseUtil.make_response(res)
        if self.DENY_FRAMES:
            response.headers['X-Frame-Options'] = 'DENY'
        return response

    def _getMethodByExceptionName(self, e):
        exception_name = {
            'NotFound': 'NotFoundError',
            'MaKaCError': 'GeneralError',
            'IndicoError': 'GeneralError',
            'ValueError': 'UnexpectedError',
            'Exception': 'UnexpectedError',
            'AccessControlError': 'AccessError'
        }.get(type(e).__name__, type(e).__name__)
        if isinstance(e, BadData):  # we also want its subclasses
            exception_name = 'BadData'
        return getattr(self, '_process{}'.format(exception_name), self._processUnexpectedError)


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
            return cls(partial(func, *args, **kwargs)).process({})

        return wrapper


class RHProtected(RH):
    def _checkSessionUser(self):
        if self._getUser() is None:
            if request.headers.get("Content-Type", "text/html").find("application/json") != -1:
                raise NotLoggedError("You are currently not authenticated. Please log in again.")
            else:
                # XXX: the next two lines are there in case something swallows our exception
                self._doProcess = False
                self._redirect(url_for_login(request.relative_url))
                raise Forbidden

    def _checkProtection(self):
        self._checkSessionUser()


class RHDisplayBaseProtected(RHProtected):
    def _checkProtection(self):
        if not isinstance(self._target, LegacyConference):
            raise Exception('Unexpected object')
        event = self._target.as_event
        can_access = event.can_access(session.user)
        if not can_access and event.access_key:
            raise KeyAccessError()
        if can_access:
            return
        elif self._getUser() is None:
            self._checkSessionUser()
        else:
            raise AccessError()


class RHModificationBaseProtected(RHProtected):
    ALLOW_LOCKED = False
    ROLE = None

    def _checkProtection(self):
        if not isinstance(self._target, LegacyConference):
            raise Exception('Unexpected object')
        event = self._target.as_event
        if not event.can_manage(session.user, role=self.ROLE):
            if self._getUser() is None:
                self._checkSessionUser()
            else:
                raise ModificationError()
        check_event_locked(self, event)


def check_event_locked(rh, event, force=False):
    if (not getattr(rh, 'ALLOW_LOCKED', False) or force) and event.is_locked and request.method not in ('GET', 'HEAD'):
        raise NoReportError.wrap_exc(Forbidden(_(u'This event has been locked so no modifications are possible.')))
