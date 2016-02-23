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

from flask import flash

from indico.modules.events.forms import EventReferencesForm
from indico.modules.events.operations import create_event_references
from indico.util.i18n import _
from indico.web.util import jsonify_data, jsonify_form
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageReferences(RHConferenceModifBase):

    CSRF_ENABLED = True

    def _process(self):
        form = EventReferencesForm(obj=FormDefaults(references=self.event_new.references))
        if form.validate_on_submit():
            create_event_references(event=self.event_new, data=form.data)
            flash(_('External IDs saved'), 'success')
            tpl = get_template_module('events/management/_reference_list.html')
            return jsonify_data(html=tpl.render_event_references_list(self.event_new.references))
        return jsonify_form(form)
