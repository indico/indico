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

from flask import redirect

from indico.modules.admin import RHAdminBase
from indico.modules.legal import legal_settings
from indico.modules.legal.forms import LegalMessagesForm
from indico.modules.legal.views import WPDisplayLegalMessages, WPManageLegalMessages
from indico.web.flask.util import url_for
from indico.legacy.webinterface.rh.base import RH


class RHManageLegalMessages(RHAdminBase):
    def _process(self):
        form = LegalMessagesForm(**legal_settings.get_all())
        if form.validate_on_submit():
            legal_settings.set_multi(form.data)
            return redirect(url_for('legal.manage'))
        return WPManageLegalMessages.render_template('manage_messages.html', 'legal_messages', form=form)


class RHDisplayLegalMessages(RH):
    def _process(self):
        return WPDisplayLegalMessages.render_template('tos.html', tos=legal_settings.get('tos'))
