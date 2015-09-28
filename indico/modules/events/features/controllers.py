# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import request, session, flash
from wtforms.fields import BooleanField

from indico.modules.events.features import logger
from indico.modules.events.features.util import (get_feature_definitions, get_enabled_features, set_feature_enabled,
                                                 get_feature_definition)
from indico.modules.events.features.views import WPFeatures
from indico.modules.events.logs import EventLogRealm, EventLogKind
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm, FormDefaults
from indico.web.forms.widgets import SwitchWidget
from indico.web.menu import render_sidemenu
from indico.web.util import jsonify_data

from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHFeaturesBase(RHConferenceModifBase):
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf

    def _process(self):
        # ConferenceModifBase overrides this with functionality that
        # doesn't even belong in there...
        return RH._process(self)


class RHFeatures(RHFeaturesBase):
    """Shows the list of available event features"""

    def _make_form(self):
        form_class = type(b'FeaturesForm', (IndicoForm,), {})
        for name, feature in sorted(get_feature_definitions().iteritems(), key=lambda x: x[1].friendly_name):
            field = BooleanField(feature.friendly_name, widget=SwitchWidget(on_label=_('On'), off_label=_('Off')),
                                 description=feature.description)
            setattr(form_class, name, field)
        defaults = {name: True for name in get_enabled_features(self.event)}
        return form_class(csrf_enabled=False, obj=FormDefaults(defaults))

    def _process(self):
        form = self._make_form()
        return WPFeatures.render_template('features.html', self.event, event=self.event, form=form)


class RHSwitchFeature(RHFeaturesBase):
    """Enables/disables a feature"""

    CSRF_ENABLED = True

    def render_event_menu(self):
        return render_sidemenu('event-management-sidemenu', active_item=WPFeatures.sidemenu_option, old_style=True,
                               event=self.event_new)

    def _process_PUT(self):
        feature = get_feature_definition(request.view_args['feature'])
        if set_feature_enabled(self.event, feature.name, True):
            flash(_('Feature enabled: {feature}').format(feature=feature.friendly_name), 'success')
            logger.info("Feature '{}' for event {} was enabled by {}".format(feature, self.event, session.user))
            self.event.log(EventLogRealm.management, EventLogKind.positive, 'Features',
                           'Enabled {}'.format(feature.friendly_name), session.user)
        return jsonify_data(enabled=True, event_menu=self.render_event_menu())

    def _process_DELETE(self):
        feature = get_feature_definition(request.view_args['feature'])
        if set_feature_enabled(self.event, feature.name, False):
            flash(_('Feature disabled: {feature}').format(feature=feature.friendly_name), 'warning')
            logger.info("Feature '{}' for event {} was disabled by {}".format(feature, self.event, session.user))
            self.event.log(EventLogRealm.management, EventLogKind.negative, 'Features',
                           'Disabled {}'.format(feature.friendly_name), session.user)
        return jsonify_data(enabled=False, event_menu=self.render_event_menu())
