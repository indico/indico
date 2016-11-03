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

from flask import flash, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.controllers.reviewing import RHAbstractReviewBase
from indico.modules.events.abstracts.operations import update_abstract
from indico.modules.events.abstracts.util import make_abstract_form
from indico.modules.events.util import get_field_values
from indico.util.i18n import _
from indico.web.util import jsonify_data, jsonify_form


class RHEditAbstract(RHAbstractReviewBase):
    def _checkProtection(self):
        RHAbstractReviewBase._checkProtection(self)
        if not self.abstract.can_edit(session.user):
            raise Forbidden

    def _process(self):
        abstract_form_class = make_abstract_form(self.event_new)
        form = abstract_form_class(obj=self.abstract, abstract=self.abstract, event=self.event_new)
        if form.validate_on_submit():
            update_abstract(self.abstract, *get_field_values(form.data))
            flash(_("Abstract modified successfully"), 'success')
            return jsonify_data(flash=False)
        self.commit = False
        return jsonify_form(form)
