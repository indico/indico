# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
from contextlib import contextmanager
from uuid import uuid4

from flask import Blueprint, Flask, g, request
from flask.blueprints import BlueprintSetupState
from flask.globals import _cv_app
from flask.testing import FlaskClient
from flask.wrappers import Request
from flask_pluginengine import PluginFlaskMixin
from flask_webpackext import current_webpack
from jinja2 import FileSystemLoader, TemplateNotFound
from jinja2.runtime import StrictUndefined
from ua_parser import user_agent_parser
from werkzeug.datastructures import ImmutableOrderedMultiDict
from werkzeug.user_agent import UserAgent
from werkzeug.utils import cached_property

from indico.core.config import config
from indico.util.json import IndicoJSONProvider
from indico.web.flask.session import IndicoSessionInterface
from indico.web.flask.templating import CustomizationLoader, IndicoEnvironment
from indico.web.flask.util import make_view_func


AUTH_BEARER_RE = re.compile(r'^Bearer (.+)$')


class ParsedUserAgent(UserAgent):
    @cached_property
    def _details(self):
        return user_agent_parser.Parse(self.string)

    @property
    def platform(self):
        return self._details['os']['family']

    @property
    def browser(self):
        return self._details['user_agent']['family']

    @property
    def version(self):
        return '.'.join(
            part
            for key in ('major', 'minor', 'patch')
            if (part := self._details['user_agent'][key]) is not None
        )


class IndicoRequest(Request):
    parameter_storage_class = ImmutableOrderedMultiDict
    user_agent_class = ParsedUserAgent

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.remote_addr is not None and self.remote_addr.startswith('::ffff:'):
            # convert ipv6-style ipv4 to the regular ipv4 notation
            self.remote_addr = self.remote_addr[7:]
        if self.remote_addr is not None and '%' in self.remote_addr:
            # remove interface specifiers in case of link-local ipv6
            self.remote_addr = self.remote_addr.split('%', 1)[0]

    @cached_property
    def id(self):
        return uuid4().hex[:16]

    @cached_property
    def relative_url(self):
        """The request's path including its query string if applicable."""
        return self.script_root + self.full_path.rstrip('?')

    @cached_property
    def bearer_token(self):
        """Bearer token included in the request, if any."""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        m = AUTH_BEARER_RE.match(auth_header)
        return m.group(1) if m else None

    @property
    def is_xhr(self):
        # XXX: avoid using this in new code; this header is non-standard and only set
        # by default in jquery, but not by anything else. check if the request accepts
        # json as an alternative.
        return self.headers.get('X-Requested-With', '').lower() == 'xmlhttprequest'


class IndicoFlaskClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__pristine = True
        self.__contexts = []

    def open(self, *args, **kwargs):
        # if we open a request for the first time, get rid of all active contexts
        # so each requests gets its own context
        if self.__pristine and self.preserve_context:
            self.__pristine = False
            while (ctx := _cv_app.get(None)):
                self.__contexts.append(ctx)
                ctx.pop()
        return super().open(*args, **kwargs)

    def __exit__(self, exc_type, exc_value, tb):
        super().__exit__(exc_type, exc_value, tb)
        # when cleaning up the test client, all contexts from the test clients have
        # been popped at this point, so we bring back the ones we saved before
        for ctx in self.__contexts[::-1]:
            ctx.push()


class IndicoFlask(PluginFlaskMixin, Flask):
    json_provider_class = IndicoJSONProvider
    request_class = IndicoRequest
    session_interface = IndicoSessionInterface()
    test_client_class = IndicoFlaskClient
    jinja_environment = IndicoEnvironment
    jinja_options = dict(Flask.jinja_options, undefined=StrictUndefined)

    @property
    def session_cookie_name(self):
        name = self.config['SESSION_COOKIE_NAME']
        if not request.is_secure:
            name += '_http'
        return name

    def create_global_jinja_loader(self):
        default_loader = super().create_global_jinja_loader()
        # use an empty list if there's no global customization dir so we can
        # add directories of plugins later once they are available
        customization_dir = os.path.join(config.CUSTOMIZATION_DIR, 'templates') if config.CUSTOMIZATION_DIR else []
        return CustomizationLoader(default_loader, customization_dir, config.CUSTOMIZATION_DEBUG)

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        from indico.web.rh import RHSimple

        # Endpoints from Flask-Multipass need to be wrapped in the RH
        # logic to get the autocommit logic and error handling for code
        # running inside the identity handler.
        if endpoint is not None and endpoint.startswith('_flaskmultipass'):
            view_func = RHSimple.wrap_function(view_func, disable_csrf_check=True)
        return super().add_url_rule(rule, endpoint=endpoint, view_func=view_func, **options)

    @property
    def has_static_folder(self):
        return False

    @property
    def manifest(self):
        if 'custom_manifests' in g:
            return g.custom_manifests[None]
        return current_webpack.manifest


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
                super().add_url_rule(rule[1:], endpoint, view_func, **options)
        else:
            super().add_url_rule(rule, endpoint, view_func, **options)


class IndicoBlueprint(Blueprint):
    """A Blueprint implementation that allows prefixing URLs with `!` to
    ignore the url_prefix of the blueprint.

    It also supports automatically creating rules in two versions - with and
    without a prefix.

    :param event_feature: If set, this blueprint will raise `NotFound`
                          for all its endpoints unless the event referenced
                          by the `event_id` URL argument has the specified
                          feature.
    """

    def __init__(self, *args, **kwargs):
        self.__prefix = None
        self.__default_prefix = ''
        self.__virtual_template_folder = kwargs.pop('virtual_template_folder', None)
        event_feature = kwargs.pop('event_feature', None)
        super().__init__(*args, **kwargs)

        if event_feature:
            @self.before_request
            def _check_event_feature():
                from indico.modules.events.features.util import require_feature
                event_id = request.view_args.get('event_id')
                if event_id is not None:
                    require_feature(event_id, event_feature)

    @cached_property
    def jinja_loader(self):
        if self.template_folder is not None:
            return IndicoFileSystemLoader(os.path.join(self.root_path, self.template_folder),
                                          virtual_path=self.__virtual_template_folder)

    def make_setup_state(self, app, options, first_registration=False):
        return IndicoBlueprintSetupState(self, app, options, first_registration)

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if view_func is not None:
            # We might have a RH class here - convert it to a callable suitable as a view func.
            view_func = make_view_func(view_func)
        super().add_url_rule(self.__default_prefix + rule, endpoint, view_func, **options)
        if self.__prefix:
            super().add_url_rule(self.__prefix + rule, endpoint, view_func, **options)

    @contextmanager
    def add_prefixed_rules(self, prefix, default_prefix=''):
        """Create prefixed rules in addition to the normal ones.

        When specifying a default_prefix, too, the normally "unprefixed" rules
        are prefixed with it.
        """
        assert self.__prefix is None and not self.__default_prefix
        self.__prefix = prefix
        self.__default_prefix = default_prefix
        yield
        self.__prefix = None
        self.__default_prefix = ''


class IndicoFileSystemLoader(FileSystemLoader):
    """FileSystemLoader that makes namespacing easier.

    The `virtual_path` kwarg lets you specify a path segment that's
    handled as if all templates inside the loader's `searchpath` were
    actually inside ``searchpath/virtual_path``.  That way you don't
    have to create subdirectories in your template folder.
    """

    def __init__(self, searchpath, encoding='utf-8', virtual_path=None):
        super().__init__(searchpath, encoding)
        self.virtual_path = virtual_path

    def list_templates(self):
        templates = super().list_templates()
        if self.virtual_path:
            templates = [os.path.join(self.virtual_path, t) for t in templates]
        return templates

    def get_source(self, environment, template):
        if self.virtual_path:
            if not template.startswith(self.virtual_path):
                raise TemplateNotFound(template)
            template = template[len(self.virtual_path):]
        return super().get_source(environment, template)
