# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.validators import DataRequired

from indico.modules.rb.event.fields import ContributionField, SessionBlockField
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm


class BookingListForm(IndicoForm):
    contribution = ContributionField(_("Contribution"), [DataRequired()],
                                     ajax_endpoint='rb.event_linkable_contributions',
                                     description=_("Enter the contribution name."))
    session_block = SessionBlockField(_("Session block"), [DataRequired()],
                                      ajax_endpoint='rb.event_linkable_session_blocks',
                                      description=_("Enter the session block name."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(BookingListForm, self).__init__(*args, **kwargs)
