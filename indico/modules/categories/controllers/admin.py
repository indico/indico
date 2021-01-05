# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, redirect

from indico.modules.admin import RHAdminBase
from indico.modules.categories import upcoming_events_settings
from indico.modules.categories.forms import UpcomingEventsForm
from indico.modules.categories.util import get_upcoming_events
from indico.modules.categories.views import WPManageUpcomingEvents
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHManageUpcomingEvents(RHAdminBase):
    def _process(self):
        form = UpcomingEventsForm(obj=FormDefaults(**upcoming_events_settings.get_all()))
        if form.validate_on_submit():
            upcoming_events_settings.set_multi(form.data)
            get_upcoming_events.clear_cached()
            flash(_('Settings saved!'), 'success')
            return redirect(url_for('categories.manage_upcoming'))
        return WPManageUpcomingEvents.render_template('admin/upcoming_events.html', 'upcoming_events', form=form)
