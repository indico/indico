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

from flask import flash, redirect

from indico.modules.admin import RHAdminBase
from indico.modules.announcement import announcement_settings
from indico.modules.announcement.forms import AnnouncementForm
from indico.modules.announcement.views import WPAnnouncement
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHAnnouncement(RHAdminBase):
    def _process(self):
        form = AnnouncementForm(obj=FormDefaults(**announcement_settings.get_all()))
        if form.validate_on_submit():
            announcement_settings.set_multi(form.data)
            flash(_('Settings have been saved'), 'success')
            return redirect(url_for('announcement.manage'))
        return WPAnnouncement.render_template('settings.html', 'announcement', form=form)
