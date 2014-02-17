# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

from contextlib import contextmanager
from flask import Flask, Blueprint
from flask.blueprints import BlueprintSetupState
from flask.wrappers import Request
from werkzeug.utils import cached_property

from MaKaC.common import HelperMaKaCInfo
from indico.web.flask.session import IndicoSessionInterface
from indico.web.flask.util import make_view_func
from indico.core.db import DBMgr

class IndicoRequest(Request):
    @cached_property
    def remote_addr(self):
        """The remote address of the client."""
        with DBMgr.getInstance().global_connection():
            if HelperMaKaCInfo.getMaKaCInfoInstance().useProxy():
                if self.access_route:
                    return self.access_route[0]
        return super(IndicoRequest, self).remote_addr

    @cached_property
    def id(self):
        return '{0:012x}'.format(id(self))

    def __repr__(self):
        rv = super(IndicoRequest, self).__repr__()
        if isinstance(rv, unicode):
            rv = rv.encode('utf-8')
        return rv


class IndicoFlask(Flask):
    request_class = IndicoRequest
    session_interface = IndicoSessionInterface()

    @property
    def debug(self):
        with DBMgr.getInstance().global_connection():
            return HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()


class IndicoBlueprintSetupState(BlueprintSetupState):
    @contextmanager
    def _unprefixed(self):
        prefix = self.url_prefix
        self.url_prefix = None
        yield
        self.url_prefix = prefix

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if rule.startswith('!/'):
            with self._unprefixed():
                super(IndicoBlueprintSetupState, self).add_url_rule(rule[1:], endpoint, view_func, **options)
        else:
            super(IndicoBlueprintSetupState, self).add_url_rule(rule, endpoint, view_func, **options)


class IndicoBlueprint(Blueprint):
    """A Blueprint implementation that allows prefixing URLs with `!` to
    ignore the url_prefix of the blueprint.

    It also supports automatically creating rules in two versions - with and
    without a prefix."""

    def __init__(self, *args, **kwargs):
        self.__prefix = None
        self.__default_prefix = ''
        super(IndicoBlueprint, self).__init__(*args, **kwargs)

    def make_setup_state(self, app, options, first_registration=False):
        return IndicoBlueprintSetupState(self, app, options, first_registration)

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if view_func is not None:
            # We might have a RH class here - convert it to a callable suitable as a view func.
            view_func = make_view_func(view_func)
        super(IndicoBlueprint, self).add_url_rule(self.__default_prefix + rule, endpoint, view_func, **options)
        if self.__prefix:
            super(IndicoBlueprint, self).add_url_rule(self.__prefix + rule, endpoint, view_func, **options)

    @contextmanager
    def add_prefixed_rules(self, prefix, default_prefix=''):
        """Creates prefixed rules in addition to the normal ones.
        When specifying a default_prefix, too, the normally "unprefixed" rules
        are prefixed with it."""
        assert self.__prefix is None and not self.__default_prefix
        self.__prefix = prefix
        self.__default_prefix = default_prefix
        yield
        self.__prefix = None
        self.__default_prefix = ''
