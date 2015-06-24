# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import request
from indico.modules.attachments.views import WPEventAttachments
from indico.modules.attachments.forms import AddAttachmentsForm, AddLinkForm
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHEventAttachments(RHConferenceModifBase):
    """Shows the attachments of an event"""

    def _process(self):
        return WPEventAttachments.render_template('attachments.html', self._conf, event=self._conf)


class RHEventAttachmentsUpload(RHConferenceModifBase):
    """Upload files"""

    def _process(self):
        form = AddAttachmentsForm()
        if request.method == 'POST':
            # TODO: Handle files
            return
        return WPEventAttachments.render_template('upload.html', self._conf, event=self._conf, form=form)


class RHEventAttachmentsAddLink(RHConferenceModifBase):
    """Attach link"""

    def _process(self):
        form = AddLinkForm()
        if form.validate_on_submit():
            # TODO
            return
        return WPEventAttachments.render_template('add_link.html', self._conf, event=self._conf, form=form)
