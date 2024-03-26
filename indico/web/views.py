# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools
import posixpath
from urllib.parse import urlparse

from flask import current_app, g, render_template, request, session
from markupsafe import Markup
from pytz import common_timezones, common_timezones_set

from indico.core import signals
from indico.core.config import config
from indico.modules.core.settings import core_settings
from indico.modules.legal import legal_settings
from indico.util.decorators import classproperty
from indico.util.i18n import _, get_all_locales
from indico.util.signals import values_from_signal
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.menu import build_menu_structure
from indico.web.util import jsonify_template


def _get_timezone_display(local_tz, timezone, force=False):
    if force and local_tz:
        return local_tz
    elif timezone == 'LOCAL':
        return local_tz or config.DEFAULT_TIMEZONE
    else:
        return timezone


def render_header(category=None, protected_object=None, local_tz=None, force_local_tz=False):
    top_menu_items = build_menu_structure('top-menu')
    return render_template('header.html',
                           category=category,
                           top_menu_items=top_menu_items,
                           protected_object=protected_object,
                           local_tz=local_tz,
                           force_local_tz=force_local_tz,
                           force_locale=None)


def render_session_bar(protected_object=None, local_tz=None, force_local_tz=False, force_locale=None,
                       force_locale_alts=None):
    protection_disclaimers = {
        'network': legal_settings.get('network_protected_disclaimer'),
        'restricted': legal_settings.get('restricted_disclaimer')
    }
    default_tz = config.DEFAULT_TIMEZONE
    if session.user:
        user_tz = session.user.settings.get('timezone', default_tz)
        if session.timezone == 'LOCAL':
            tz_mode = 'local'
        elif session.timezone == user_tz:
            tz_mode = 'user'
        else:
            tz_mode = 'custom'
    else:
        user_tz = None
        tz_mode = 'local' if session.timezone == 'LOCAL' else 'custom'
    active_tz = _get_timezone_display(local_tz, session.timezone, force_local_tz)
    timezones = common_timezones
    if active_tz not in common_timezones_set:
        timezones = [*common_timezones, active_tz]
    timezone_data = {
        'disabled': force_local_tz,
        'user_tz': user_tz,
        'active_tz': active_tz,
        'tz_mode': tz_mode,
        'timezones': timezones,
    }
    tpl = get_template_module('_session_bar.html')
    rv = tpl.render_session_bar(protected_object=protected_object,
                                protection_disclaimers=protection_disclaimers,
                                timezone_data=timezone_data,
                                languages=get_all_locales(),
                                force_locale=force_locale,
                                force_locale_alts=force_locale_alts)
    return Markup(rv)


class WPJinjaMixin:
    """Mixin for WPs backed by Jinja templates.

    This allows you to use a single WP class and its layout, CSS,
    etc. for multiple pages in a lightweight way while still being
    able to use a subclass if more.

    To avoid collisions between blueprint and application templates,
    your blueprint template folders should have a subfolder named like
    the blueprint. To avoid writing it all the time, you can store it
    as `template_prefix` (with a trailing slash) in your WP class.
    This only applies to the indico core as plugins always use a separate
    template namespace!
    """

    # you can set `ALLOW_JSON = False` to disable sending a jsonified
    # version for XHR requests.  the attribute is not set here on the class
    # because the current inheritance chain would make it impossible to
    # change it on some base classes such as `WPEventBase` as this mixin
    # is used deeper down in the hierarchy

    template_prefix = ''
    render_template_func = staticmethod(render_template)

    @classmethod
    def render_template(cls, template_name_or_list=None, *wp_args, **context):
        """Render a jinja template inside the WP.

        :param template_name_or_list: the name of the template - if unsed, the
                                      `_template` attribute of the class is used.
                                      can also be a list containing multiple
                                      templates (the first existing one is used)
        :param wp_args: list of arguments to be passed to the WP's' constructor
        :param context: the variables that should be available in the context of
                        the template
        """
        template = cls._prefix_template(template_name_or_list or cls._template)
        if getattr(cls, 'ALLOW_JSON', True) and request.is_xhr:
            return jsonify_template(template, _render_func=cls.render_template_func, **context)
        else:
            context['_jinja_template'] = template
            return cls(g.rh, *wp_args, **context).display()

    @classmethod
    def render_string(cls, html, *wp_args):
        """Render a string inside the WP.

        :param html: a string containing html
        :param wp_args: list of arguments to be passed to the WP's' constructor
        """
        return cls(g.rh, *wp_args, _html=html).display()

    @classmethod
    def _prefix_template(cls, template):
        if cls.template_prefix and cls.template_prefix[-1] != '/':
            raise ValueError('template_prefix needs to end with a slash')
        if isinstance(template, str):
            return cls.template_prefix + template
        else:
            templates = []
            for tpl in template:
                pos = tpl.find(':') + 1
                templates.append(tpl[:pos] + cls.template_prefix + tpl[pos:])
            return templates

    def _get_page_content(self, params):
        html = params.pop('_html', None)
        if html is not None:
            return html
        template = params.pop('_jinja_template')
        params['bundles'] = (current_app.manifest[x] for x in self._resolve_bundles())
        return self.render_template_func(template, **params)


class WPBundleMixin:
    bundles = ('exports.js', 'common-runtime.js')
    print_bundles = ()

    @classproperty
    @classmethod
    def additional_bundles(cls):
        """Additional bundle objects that will be included."""
        return {
            'screen': (),
            'print': ()
        }

    @classmethod
    def _resolve_bundles(cls):
        """Add up all bundles, following the MRO."""
        seen_bundles = set()
        for class_ in reversed(cls.mro()[:-1]):
            attr = class_.__dict__.get('bundles', ())
            if isinstance(attr, classproperty):
                attr = attr.__get__(None, class_)
            elif isinstance(attr, property):
                attr = attr.fget(cls)

            for bundle in attr:
                if config.DEBUG and bundle in seen_bundles:
                    raise Exception(f"Duplicate bundle found in {class_.__name__}: '{bundle}'")
                seen_bundles.add(bundle)
                yield bundle

    @classproperty
    @classmethod
    def page_metadata(cls):
        site_name = core_settings.get('site_title')
        return {
            'og': {
                'site_name': (site_name + ' (Indico)') if site_name != 'Indico' else site_name,
                'image': url_for('assets.image', filename='indico_square.png', _external=True)
            }
        }

    @classproperty
    @classmethod
    def tinymce_content_css_urls(cls):
        tinymce_css_bundles = ('common.css', 'react.css', 'semantic-ui.css', 'jquery.css', 'main.css')
        return list(itertools.chain.from_iterable(current_app.manifest[x] for x in tinymce_css_bundles))


class WPBase(WPBundleMixin):
    title = ''

    #: Whether the WP is used for management (adds suffix to page title)
    MANAGEMENT = False

    def __init__(self, rh, **kwargs):
        self._rh = rh
        self._kwargs = kwargs

    def get_extra_css_files(self):
        """Return CSS urls that will be included after all other CSS."""
        return []

    def get_extra_js_files(self):
        """Return JS urls that will be included after all other JS."""
        return []

    @classproperty
    @classmethod
    def bundles(cls):
        return ('common.css', 'common.js', 'react.css', 'react.js', 'semantic-ui.js', 'semantic-ui.css',
                'jquery.css', 'jquery.js', 'main.css', 'main.js', 'module_core.js', 'module_events.creation.js',
                'module_attachments.js', 'outdatedbrowser.js', 'outdatedbrowser.css')

    def _get_head_content(self):
        """Return _additional_ content between <head></head> tags.

        Please note that <title>, <meta> and standard CSS are always included.
        Override this method to add your own, page-specific loading of
        JavaScript, CSS and other legal content for HTML <head> tag.
        """
        return ''

    def _fix_path(self, path):
        url_path = urlparse(config.BASE_URL).path or '/'
        # append base path only if not absolute already
        # and not in 'static site' mode (has to be relative)
        if path[0] != '/' and not g.get('static_site'):
            path = posixpath.join(url_path, path)
        return path

    def _display(self, params):
        raise NotImplementedError

    @property
    def _extra_title_parts(self):
        return ()

    def display(self, **params):
        from indico.modules.admin import RHAdminBase
        from indico.modules.core.settings import core_settings

        title_parts = [*self._extra_title_parts, self.title]
        if self.MANAGEMENT:
            title_parts.insert(0, _('Management'))
        elif isinstance(self._rh, RHAdminBase):
            title_parts.insert(0, _('Administration'))

        injected_bundles = values_from_signal(signals.plugin.inject_bundle.send(self.__class__), as_list=True,
                                              multi_value_types=list)
        custom_js = list(current_app.manifest['__custom.js'])
        custom_css = list(current_app.manifest['__custom.css'])
        css_files = list(map(self._fix_path, self.get_extra_css_files() + custom_css))
        js_files = list(map(self._fix_path, self.get_extra_js_files() + custom_js))

        body = self._display(params)
        bundles = itertools.chain((current_app.manifest[x] for x in self._resolve_bundles()
                                   if x in current_app.manifest._entries),
                                  self.additional_bundles['screen'], injected_bundles)
        print_bundles = itertools.chain((current_app.manifest[x] for x in self.print_bundles),
                                        self.additional_bundles['print'])

        return render_template('indico_base.html',
                               css_files=css_files, js_files=js_files,
                               bundles=bundles, print_bundles=print_bundles,
                               tinymce_content_css_urls=self.tinymce_content_css_urls,
                               site_name=core_settings.get('site_title'),
                               page_metadata=self.page_metadata,
                               page_title=' - '.join(str(x) for x in title_parts if x),
                               head_content=self._get_head_content(),
                               body=body, wp_class=type(self))


class WPNewBase(WPBundleMixin, WPJinjaMixin):
    title = ''
    bundles = ('outdatedbrowser.js', 'outdatedbrowser.css')
    print_bundles = ()

    #: Whether the WP is used for management (adds suffix to page title)
    MANAGEMENT = False

    def __init__(self, rh, **kwargs):
        self._rh = rh
        self._kwargs = kwargs

    @classmethod
    def _fix_path(cls, path):
        url_path = urlparse(config.BASE_URL).path or '/'
        # append base path only if not absolute already
        # and not in 'static site' mode (has to be relative)
        if path[0] != '/' and not g.get('static_site'):
            path = posixpath.join(url_path, path)
        return path

    @classmethod
    def display(cls, template_name, **params):
        from indico.modules.admin import RHAdminBase
        from indico.modules.core.settings import core_settings

        title_parts = [cls.title]
        if cls.MANAGEMENT:
            title_parts.insert(0, _('Management'))
        elif isinstance(g.rh, RHAdminBase):
            title_parts.insert(0, _('Administration'))

        injected_bundles = values_from_signal(signals.plugin.inject_bundle.send(cls), as_list=True,
                                              multi_value_types=list)
        custom_js = list(current_app.manifest['__custom.js'])
        custom_css = list(current_app.manifest['__custom.css'])
        css_files = list(map(cls._fix_path, custom_css))
        js_files = list(map(cls._fix_path, custom_js))

        bundles = itertools.chain((current_app.manifest[x] for x in cls._resolve_bundles()
                                   if x in current_app.manifest._entries),
                                  cls.additional_bundles['screen'], injected_bundles)
        print_bundles = itertools.chain((current_app.manifest[x] for x in cls.print_bundles),
                                        cls.additional_bundles['print'])
        template = cls._prefix_template(template_name)
        return render_template(template,
                               css_files=css_files, js_files=js_files,
                               page_metadata=cls.page_metadata,
                               bundles=bundles, print_bundles=print_bundles,
                               tinymce_content_css_urls=cls.tinymce_content_css_urls,
                               site_name=core_settings.get('site_title'),
                               page_title=' - '.join(str(x) for x in title_parts if x),
                               wp_class=cls,
                               **params)


class WPDecorated(WPBase):
    sidemenu_option = None

    def _get_header(self):
        return render_header()

    def _get_footer(self):
        return render_template('footer.html')

    def _apply_decoration(self, body):
        breadcrumbs = self._get_breadcrumbs()
        header = self._get_header()
        footer = self._get_footer()
        return f'<div class="header">{header}</div>\n<main class="main">{breadcrumbs}<div>{body}</div></main>\n{footer}'

    def _display(self, params):
        return self._apply_decoration(self._get_body(params | self._kwargs))

    def _get_body(self, params):
        raise NotImplementedError

    def _get_breadcrumbs(self):
        return ''


class WPError(WPDecorated, WPJinjaMixin):
    def __init__(self, message, description):
        WPDecorated.__init__(self, None)
        self._message = message
        self._description = description

    def _get_body(self, params):
        return self._get_page_content({
            '_jinja_template': 'error.html',
            'error_message': self._message,
            'error_description': self._description
        })
