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

from __future__ import unicode_literals

from flask import request, session, flash
from werkzeug.exceptions import Forbidden
from wtforms.fields import BooleanField

from indico.modules.events.features import logger
from indico.modules.events.features.util import (get_feature_definitions, get_enabled_features, set_feature_enabled,
                                                 get_feature_definition, get_disallowed_features, format_feature_names)
from indico.modules.events.features.views import WPFeatures
from indico.modules.events.logs import EventLogRealm, EventLogKind
from indico.util.i18n import _, ngettext
from indico.web.forms.base import IndicoForm, FormDefaults
from indico.web.forms.widgets import SwitchWidget
from indico.web.menu import render_sidemenu
from indico.web.util import jsonify_data

from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHFeaturesBase(RHConferenceModifBase):
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)

    def _process(self):
        # ConferenceModifBase overrides this with functionality that
        # doesn't even belong in there...
        return RH._process(self)


class RHFeatures(RHFeaturesBase):
    """Shows the list of available event features"""

    def _make_form(self):
        form_class = type(b'FeaturesForm', (IndicoForm,), {})
        disallowed = get_disallowed_features(self.event_new)
        for name, feature in sorted(get_feature_definitions().iteritems(), key=lambda x: x[1].friendly_name):
            if name in disallowed:
                continue
            field = BooleanField(feature.friendly_name, widget=SwitchWidget(on_label=_('On'), off_label=_('Off')),
                                 description=feature.description)
            setattr(form_class, name, field)
        defaults = {name: True for name in get_enabled_features(self.event_new)}
        return form_class(csrf_enabled=False, obj=FormDefaults(defaults))

    def _process(self):
        form = self._make_form()
        return WPFeatures.render_template('features.html', self._conf, event=self.event_new, form=form)


class RHSwitchFeature(RHFeaturesBase):
    """Enables/disables a feature"""

    CSRF_ENABLED = True

    def render_event_menu(self):
        return render_sidemenu('event-management-sidemenu', active_item=WPFeatures.sidemenu_option,
                               event=self.event_new)

    def _process_PUT(self):
        prev = get_enabled_features(self.event_new)
        feature = get_feature_definition(request.view_args['feature'])
        if feature.name in get_disallowed_features(self.event_new):
            raise Forbidden('Feature not available')
        changed = set()
        if set_feature_enabled(self.event_new, feature.name, True):
            current = get_enabled_features(self.event_new)
            changed = current - prev
            flash(ngettext('Feature enabled: {features}', 'Features enabled: {features}', len(changed))
                  .format(features=format_feature_names(changed)), 'success')
            logger.info("Feature '%s' for event %s enabled by %s", feature.name, self.event_new, session.user)
            self.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Features',
                               'Enabled {}'.format(feature.friendly_name), session.user)
        return jsonify_data(enabled=True, event_menu=self.render_event_menu(), changed=list(changed))

    def _process_DELETE(self):
        prev = get_enabled_features(self.event_new)
        feature = get_feature_definition(request.view_args['feature'])
        changed = set()
        if set_feature_enabled(self.event_new, feature.name, False):
            current = get_enabled_features(self.event_new)
            changed = prev - current
            flash(ngettext('Feature disabled: {features}', 'Features disabled: {features}', len(changed))
                  .format(features=format_feature_names(changed)), 'warning')
            logger.info("Feature '%s' for event %s disabled by %s", feature.name, self.event_new, session.user)
            self.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Features',
                               'Disabled {}'.format(feature.friendly_name), session.user)
        return jsonify_data(enabled=False, event_menu=self.render_event_menu(), changed=list(changed))
