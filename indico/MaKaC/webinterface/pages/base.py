# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import posixpath
from urlparse import urlparse

from flask import request, session, render_template, g

import MaKaC.webinterface.wcomponents as wcomponents
from indico.core import signals
from indico.web import assets
from indico.core.config import Config
from indico.modules.auth.util import url_for_login, url_for_logout
from indico.util.i18n import i18nformat
from indico.util.signals import values_from_signal
from indico.util.string import to_unicode, encode_if_unicode
from indico.web.util import jsonify_template
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.i18n import _


class WPJinjaMixin:
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
        if request.is_xhr:
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


class WPBase():
    """
    """
    _title = "Indico"

    # required user-specific "data packages"
    _userData = []

    #: Whether the WP is used for management (adds suffix to page title)
    MANAGEMENT = False

    def __init__(self, rh, _protected_object=None, _current_category=None, **kwargs):
        config = Config.getInstance()
        self._rh = rh
        self._kwargs = kwargs
        self._locTZ = ""

        self._dir = config.getTPLDir()
        self._asset_env = assets.core_env
        self._protected_object = _protected_object
        self._current_category = _current_category

        #store page specific CSS and JS
        self._extraCSS = []

    def _getBaseURL(self):
        if request.is_secure and Config.getInstance().getBaseSecureURL():
            return Config.getInstance().getBaseSecureURL()
        else:
            return Config.getInstance().getBaseURL()

    def _getTitle(self):
        return self._title

    def _setTitle(self, newTitle):
        self._title = newTitle.strip()

    def getPrintCSSFiles(self):
        return []

    def getCSSFiles(self):
        return (self._asset_env['base_css'].urls() +
                self._asset_env['dropzone_css'].urls() +
                self._asset_env['screen_sass'].urls() +
                self._asset_env['attachments_sass'].urls() +
                self._asset_env['users_sass'].urls())

    def get_extra_css_files(self):
        """Return CSS urls that will be included after all other CSS"""
        return []

    def getJSFiles(self):
        return (self._asset_env['base_js'].urls() +
                self._asset_env['dropzone_js'].urls() +
                self._asset_env['modules_attachments_js'].urls())

    def _includeJSPackage(self, pkg_names, prefix='indico_'):
        if not isinstance(pkg_names, list):
            pkg_names = [pkg_names]

        return [url
                for pkg_name in pkg_names
                for url in self._asset_env[prefix + pkg_name.lower()].urls()]

    def _getHeadContent( self ):
        """
        Returns _additional_ content between <head></head> tags.
        Please note that <title>, <meta> and standard CSS are always included.

        Override this method to add your own, page-specific loading of
        JavaScript, CSS and other legal content for HTML <head> tag.
        """
        return ""

    def _getWarningMessage(self):
        return ""

    def _getHTMLHeader( self ):
        from MaKaC.webinterface.rh.base import RHModificationBaseProtected
        from MaKaC.webinterface.rh.admins import RHAdminBase

        area=""
        if self.MANAGEMENT or isinstance(self._rh, RHModificationBaseProtected):
            area=i18nformat(""" - _("Management area")""")
        elif isinstance(self._rh, RHAdminBase):
            area=i18nformat(""" - _("Administrator area")""")

        info = HelperMaKaCInfo().getMaKaCInfoInstance()

        plugin_css = values_from_signal(signals.plugin.inject_css.send(self.__class__), as_list=True,
                                        multi_value_types=list)
        plugin_js = values_from_signal(signals.plugin.inject_js.send(self.__class__), as_list=True,
                                       multi_value_types=list)

        return wcomponents.WHTMLHeader().getHTML({
            "area": area,
            "baseurl": self._getBaseURL(),
            "conf": Config.getInstance(),
            "page": self,
            "printCSS": map(self._fix_path, self.getPrintCSSFiles()),
            "extraCSS": map(self._fix_path, self.getCSSFiles() + plugin_css + self.get_extra_css_files()),
            "extraJSFiles": map(self._fix_path, self.getJSFiles() + plugin_js),
            "language": session.lang or info.getLang(),
            "social": info.getSocialAppConfig(),
            "assets": self._asset_env
        })

    def _fix_path(self, path):
        url_path = urlparse(Config.getInstance().getBaseURL()).path or '/'
        if path[0] != '/':
            path = posixpath.join(url_path, path)
        return path

    def _getHTMLFooter( self ):
        return """
    </body>
</html>
               """

    def _display( self, params ):
        """
        """
        return _("no content")

    def _getAW( self ):
        return self._rh.getAW()

    def display( self, **params ):
        """
        """
        return "%s%s%s" % (self._getHTMLHeader(),
                           encode_if_unicode(self._display(params)),
                           self._getHTMLFooter())


    # auxiliar functions
    def _escapeChars(self, text):
        # Not doing anything right now - it used to convert % to %% for old-style templates
        return text


class WPDecorated(WPBase):

    def _getSiteArea(self):
        return "DisplayArea"

    def getLoginURL( self ):
        return url_for_login(next_url=request.relative_url)

    def getLogoutURL( self ):
        return url_for_logout(next_url=request.relative_url)

    def _getHeader(self):
        wc = wcomponents.WHeader(self._getAW(), isFrontPage=self._isFrontPage(), locTZ=self._locTZ,
                                 currentCategory=self._current_category, prot_obj=self._protected_object)

        return wc.getHTML( { "subArea": self._getSiteArea(), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())) } )

    def _getTabControl(self):
        return None

    def _getFooter( self):
        """
        """
        wc = wcomponents.WFooter(isFrontPage=self._isFrontPage())
        return wc.getHTML({ "subArea": self._getSiteArea() })

    def _applyDecoration(self, body):
        return u'<div class="header">{}</div><div class="main">{}</div><div class="footer">{}</div>'.format(
            to_unicode(self._getHeader()), to_unicode(body), to_unicode(self._getFooter()))

    def _display(self, params):
        params = dict(params, **self._kwargs)
        return self._applyDecoration(self._getBody(params))

    def _getBody( self, params ):
        """
        """
        pass

    def _getNavigationDrawer(self):
        return None

    def _isFrontPage(self):
        """
            Welcome page class overloads this, so that additional info (news, policy)
            is shown.
        """
        return False

    def _isRoomBooking(self):
        return False


class WPNotDecorated(WPBase):

    def getLoginURL(self):
        return url_for_login(next_url=request.relative_url)

    def getLogoutURL(self):
        return url_for_logout(next_url=request.relative_url)

    def _display(self, params):
        params = dict(params, **self._kwargs)
        return self._getBody(params)

    def _getBody(self, params):
        pass

    def _getNavigationDrawer(self):
        return None
