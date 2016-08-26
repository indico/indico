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

from flask import redirect, flash, jsonify

from indico.modules.events.abstracts.forms import BOASettingsForm
from indico.modules.events.abstracts.settings import boa_settings
from indico.modules.events.abstracts.operations import create_abstract
from indico.modules.events.abstracts.util import AbstractListGenerator, make_abstract_form
from indico.modules.events.abstracts.views import WPManageAbstracts
from indico.modules.events.util import _get_field_values
from indico.util.i18n import _
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageAbstractsBase(RHConferenceModifBase):
    """Base class for all abstracts management RHs"""

    CSRF_ENABLED = True
    EVENT_FEATURE = 'abstracts'

    def _process(self):
        return RH._process(self)


class RHAbstractListBase(RHManageAbstractsBase):
    """Base class for all abstract list operations"""

    def _checkParams(self, params):
        RHManageAbstractsBase._checkParams(self, params)
        self.list_generator = AbstractListGenerator(event=self.event_new)


class RHAbstracts(RHManageAbstractsBase):
    """Display abstracts management page"""

    def _process(self):
        return WPManageAbstracts.render_template('management/abstracts.html', self._conf, event=self.event_new)


class RHManageBOA(RHManageAbstractsBase):
    """Configure book of abstracts"""

    def _process(self):
        form = BOASettingsForm(obj=FormDefaults(**boa_settings.get_all(self.event_new)))
        if form.validate_on_submit():
            boa_settings.set_multi(self.event_new, form.data)
            flash(_('Book of Abstract settings have been saved'), 'success')
            return jsonify_data()
        return jsonify_form(form)


class RHAbstractList(RHAbstractListBase):
    """Display the list of abstracts"""

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        list_kwargs = self.list_generator.get_list_kwargs()
        return WPManageAbstracts.render_template('management/abstract_list.html', self._conf, event=self.event_new,
                                                 **list_kwargs)


class RHAbstractListCustomize(RHAbstractListBase):
    """Filter options and columns to display for the abstract list of an event"""

    def _process_GET(self):
        list_config = self.list_generator._get_config()
        return WPManageAbstracts.render_template('management/abstract_list_filter.html', self._conf,
                                                 event=self.event_new, visible_items=list_config['items'],
                                                 static_items=self.list_generator.static_items,
                                                 filters=list_config['filters'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())


class RHAbstractListStaticURL(RHAbstractListBase):
    """Generate a static URL for the configuration of the abstract list"""

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHCreateAbstract(RHAbstractListBase):
    def _process(self):
        abstract_form_class = make_abstract_form(self.event_new)
        form = abstract_form_class(event=self.event_new)
        if form.validate_on_submit():
            abstract = create_abstract(self.event_new, *_get_field_values(form.data))
            flash(_("Abstract '{}' created successfully").format(abstract.title), 'success')
            tpl_components = self.list_generator.render_list()
            if tpl_components.get('hide_abstract'):
                self.list_generator.flash_info_message(abstract)
            return jsonify_data(**tpl_components)
        return jsonify_template('events/abstracts/forms/abstract.html', form=form)
