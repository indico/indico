# This file is part of Indico.
# Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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

from wtforms.validators import DataRequired

from indico.modules.rb_new.event.fields import ContributionField, SessionBlockField
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm


class BookingListForm(IndicoForm):
    contribution = ContributionField(_("Contribution"), [DataRequired()],
                                     ajax_endpoint='rooms_new.event_linkable_contributions',
                                     description=_("Enter the contribution name."))
    session_block = SessionBlockField(_("Session block"), [DataRequired()],
                                      ajax_endpoint='rooms_new.event_linkable_session_blocks',
                                      description=_("Enter the session block name."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(BookingListForm, self).__init__(*args, **kwargs)
