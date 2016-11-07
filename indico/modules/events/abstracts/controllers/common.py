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

from flask import flash, session, request

from indico.modules.events.abstracts.controllers.base import RHAbstractBase, render_abstract_page
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.operations import update_abstract
from indico.modules.events.abstracts.util import make_abstract_form
from indico.modules.events.abstracts.views import WPDisplayAbstracts, WPManageAbstracts
from indico.modules.events.util import get_field_values
from indico.util.i18n import _
from indico.web.util import jsonify_data, jsonify_form


class RHDisplayAbstract(RHAbstractBase):
    @property
    def view_class(self):
        return WPManageAbstracts if self.management else WPDisplayAbstracts

    def _process(self):
        return render_abstract_page(self.abstract, view_class=self.view_class, management=self.management)


class RHEditAbstract(RHAbstractBase):
    def _check_abstract_protection(self):
        return self.abstract.can_edit(session.user)

    def _process(self):
        abstract_form_class = make_abstract_form(self.event_new)
        form = abstract_form_class(obj=self.abstract, abstract=self.abstract, event=self.event_new)
        if form.validate_on_submit():
            update_abstract(self.abstract, *get_field_values(form.data))
            flash(_("Abstract modified successfully"), 'success')
            return jsonify_data(flash=False)
        self.commit = False
        disabled_fields = ('submitted_for_tracks',) if form.track_field_disabled else ()
        return jsonify_form(form, disabled_fields=disabled_fields)


class RHAbstractsDownloadAttachment(RHAbstractBase):
    """Download an attachment file belonging to an abstract."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract_file
        }
    }

    def _checkParams(self, params):
        RHAbstractBase._checkParams(self, params)
        self.abstract_file = AbstractFile.get_one(request.view_args['file_id'])

    def _process(self):
        return self.abstract_file.send()
