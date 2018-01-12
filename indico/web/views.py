# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import posixpath
from urlparse import urlparse

from flask import g, render_template, request, session
from markupsafe import Markup
from pytz import common_timezones, common_timezones_set

from indico.core import signals
from indico.core.config import config
from indico.legacy.webinterface.wcomponents import render_header
from indico.modules.legal import legal_settings
from indico.util.i18n import _, get_all_locales
from indico.util.signals import values_from_signal
from indico.util.string import to_unicode
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_template


def _get_timezone_display(local_tz, timezone, force=False):
    if force and local_tz:
        return local_tz
    elif timezone == 'LOCAL':
        return local_tz or config.DEFAULT_TIMEZONE
    else:
        return timezone


def render_session_bar(protected_object=None, local_tz=None, force_local_tz=False):
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
        timezones = list(common_timezones) + [active_tz]
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
                                languages=get_all_locales())
    return Markup(rv)


class WPJinjaMixin(object):
    """Mixin for WPs backed by Jinja templates.

    This allows you to use a single WP class and its layout, CSS,
    etc. for multiple pages in a lightweight way while still being
    able to use a subclass if more.

    To avoid collisions between blueprint and application templates,
    your blueprint template folders should have a subfolder named like
    the blueprint. To avoid writing it all the time, you can store it
    as `template_prefix` (with a trailing slash) in yor WP class.
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
        """Renders a jinja template inside the WP

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
        """Renders a string inside the WP

        :param html: a string containing html
        :param wp_args: list of arguments to be passed to the WP's' constructor
        """
        return cls(g.rh, *wp_args, _html=html).display()

    @classmethod
    def _prefix_template(cls, template):
        if isinstance(template, basestring):
            return cls.template_prefix + template
        else:
            templates = []
            for tpl in template:
                pos = tpl.find(':') + 1
                templates.append(tpl[:pos] + cls.template_prefix + tpl[pos:])
            return templates

    def _getPageContent(self, params):
        html = params.pop('_html', None)
        if html is not None:
            return html
        template = params.pop('_jinja_template')
        return self.render_template_func(template, **params)


class WPBase(object):
    title = ''

    #: Whether the WP is used for management (adds suffix to page title)
    MANAGEMENT = False

    def __init__(self, rh, **kwargs):
        from indico.web.assets import core_env
        self._rh = rh
        self._kwargs = kwargs
        self._asset_env = core_env

    def getPrintCSSFiles(self):
        return []

    def getCSSFiles(self):
        return (self._asset_env['base_css'].urls() +
                self._asset_env['dropzone_css'].urls() +
                self._asset_env['screen_sass'].urls())

    def get_extra_css_files(self):
        """Return CSS urls that will be included after all other CSS"""
        return []

    def getJSFiles(self):
        ckeditor_js = self._asset_env['ckeditor'].urls() if not g.get('static_site') else []
        return (self._asset_env['base_js'].urls() +
                ckeditor_js +
                self._asset_env['dropzone_js'].urls() +
                self._asset_env['modules_attachments_js'].urls())

    def _includeJSPackage(self, pkg_names, prefix='indico_'):
        if not isinstance(pkg_names, list):
            pkg_names = [pkg_names]

        return [url
                for pkg_name in pkg_names
                for url in self._asset_env[prefix + pkg_name.lower()].urls()]

    def _getHeadContent(self):
        """
        Returns _additional_ content between <head></head> tags.
        Please note that <title>, <meta> and standard CSS are always included.

        Override this method to add your own, page-specific loading of
        JavaScript, CSS and other legal content for HTML <head> tag.
        """
        return ""

    def _fix_path(self, path):
        url_path = urlparse(config.BASE_URL).path or '/'
        if path[0] != '/':
            path = posixpath.join(url_path, path)
        return path

    def _display(self, params):
        raise NotImplementedError

    def display(self, **params):
        from indico.modules.admin import RHAdminBase
        from indico.modules.core.settings import core_settings, social_settings

        title_parts = [self.title]
        if self.MANAGEMENT:
            title_parts.insert(0, _('Management'))
        elif isinstance(self._rh, RHAdminBase):
            title_parts.insert(0, _('Administration'))

        plugin_css = values_from_signal(signals.plugin.inject_css.send(self.__class__), as_list=True,
                                        multi_value_types=list)
        plugin_js = values_from_signal(signals.plugin.inject_js.send(self.__class__), as_list=True,
                                       multi_value_types=list)
        custom_js = self._asset_env['custom_js'].urls() if 'custom_js' in self._asset_env else []
        custom_css = self._asset_env['custom_sass'].urls() if 'custom_sass' in self._asset_env else []
        css_files = map(self._fix_path, self.getCSSFiles() + plugin_css + self.get_extra_css_files() + custom_css)
        print_css_files = map(self._fix_path, self.getPrintCSSFiles())
        js_files = map(self._fix_path, self.getJSFiles() + plugin_js + custom_js)

        body = to_unicode(self._display(params))

        return render_template('indico_base.html',
                               css_files=css_files, print_css_files=print_css_files, js_files=js_files,
                               site_name=core_settings.get('site_title'),
                               social=social_settings.get_all(),
                               page_title=' - '.join(unicode(x) for x in title_parts if x),
                               head_content=to_unicode(self._getHeadContent()),
                               body=body)


class WPDecorated(WPBase):
    sidemenu_option = None

    def _getHeader(self):
        return render_header()

    def _getTabControl(self):
        return None

    def _getFooter(self):
        return render_template('footer.html').encode('utf-8')

    def _applyDecoration(self, body):
        breadcrumbs = self._get_breadcrumbs()
        return '<div class="header">{}</div>\n<div class="main">{}<div>{}</div></div>\n{}'.format(
            to_unicode(self._getHeader()), breadcrumbs, to_unicode(body), to_unicode(self._getFooter()))

    def _display(self, params):
        params = dict(params, **self._kwargs)
        return self._applyDecoration(self._getBody(params))

    def _getBody(self, params):
        raise NotImplementedError

    def _get_breadcrumbs(self):
        return ''


class WPNotDecorated(WPBase):
    def _display(self, params):
        params = dict(params, **self._kwargs)
        return self._getBody(params)

    def _getBody(self, params):
        pass

    def _get_breadcrumbs(self):
        return ''


class WPError(WPDecorated, WPJinjaMixin):
    def __init__(self, message, description):
        WPDecorated.__init__(self, None)
        self._message = message
        self._description = description

    def _getBody(self, params):
        return self._getPageContent({
            '_jinja_template': 'error.html',
            'error_message': self._message,
            'error_description': self._description
        })

    def getHTML(self):
        return self.display()
