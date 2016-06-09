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

from indico.modules.legal import settings
from indico.modules.legal.forms import LegalMessagesForm
from indico.modules.legal.views import WPManageLegalMessages
from MaKaC.webinterface.rh.admins import RHAdminBase


class RHManageLegalMessages(RHAdminBase):

    def _process(self):
        form = LegalMessagesForm(**settings.get_all())
        if form.validate_on_submit():
            for field in form.visible_fields:
                settings.set(field.name, getattr(form, field.name).data)
        return WPManageLegalMessages.render_template('manage_messages.html', form=form)
