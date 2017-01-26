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

from __future__ import unicode_literals

from flask import flash
from werkzeug.urls import url_join

from indico.core.config import Config
from indico.modules.cephalopod import settings as cephalopod_settings
from indico.modules.core.forms import SiteSettingsForm, SocialSettingsForm
from indico.modules.core.settings import core_settings, social_settings
from indico.modules.core.views import WPSettings
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_form, jsonify_data
from MaKaC.webinterface.rh.admins import RHAdminBase


class RHCoreAdminBase(RHAdminBase):
    CSRF_ENABLED = True


class RHSettings(RHCoreAdminBase):
    """General settings"""

    def _get_cephalopod_data(self):
        if not cephalopod_settings.get('joined'):
            return None, {'enabled': False}

        url = url_join(Config.getInstance().getTrackerURL(), 'api/instance/{}'.format(cephalopod_settings.get('uuid')))
        data = {'enabled': cephalopod_settings.get('joined'),
                'contact': cephalopod_settings.get('contact_name'),
                'email': cephalopod_settings.get('contact_email'),
                'url': Config.getInstance().getBaseURL(),
                'organisation': core_settings.get('site_organization')}
        return url, data

    def _process(self):
        cephalopod_url, cephalopod_data = self._get_cephalopod_data()
        return WPSettings.render_template('settings.html',
                                          core_settings=core_settings.get_all(),
                                          social_settings=social_settings.get_all(),
                                          cephalopod_url=cephalopod_url,
                                          cephalopod_data=cephalopod_data)


class RHSettingsBase(RHCoreAdminBase):
    """Base class to edit settings"""

    form_class = None
    macro = None
    settings_proxy = None

    def _process(self):
        form = self.form_class(obj=FormDefaults(**self.settings_proxy.get_all()))
        if form.validate_on_submit():
            self.settings_proxy.set_multi(form.data)
            flash(_('Settings have been saved'), 'success')
            tpl = get_template_module('core/_settings.html')
            return jsonify_data(html=getattr(tpl, self.macro)(self.settings_proxy.get_all()))
        return jsonify_form(form)


class RHSiteSettings(RHSettingsBase):
    """Edit site settings"""

    form_class = SiteSettingsForm
    settings_proxy = core_settings
    macro = 'render_site_settings'


class RHSocialSettings(RHSettingsBase):
    """Edit social settings"""

    form_class = SocialSettingsForm
    settings_proxy = social_settings
    macro = 'render_social_settings'
