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

from flask import flash, session

from indico.util.i18n import _
from indico.web.flask.util import url_for, jsonify_data
from indico.web.util import jsonify_template

from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHDeleteEventForm(RHConferenceModifBase):
    """Delete an event."""

    def _process(self):
        return jsonify_template('events/management/delete_event.html', event=self._conf)


class RHDeleteEventAction(RHConferenceModifBase):
    """Delete an event."""

    CSRF_ENABLED = True

    def _process(self):
        category = self._conf.getOwner()

        self._conf.delete(session.user)
        flash(_('Event "{}" successfully deleted.').format(self._conf.title), 'success')

        if category:
            redirect_url = url_for('category_mgmt.categoryModification', category)
        else:
            redirect_url = url_for('misc.index')

        return jsonify_data(url=redirect_url, flash=False)


class RHLockEventForm(RHConferenceModifBase):
    """Lock an event."""

    def _process(self):
        return jsonify_template('events/management/lock_event.html', event=self._conf)


class RHLockEventAction(RHConferenceModifBase):
    """Lock an event."""

    CSRF_ENABLED = True

    def _process(self):
        self._conf.setClosed(True)
        flash(_('The event is now locked.').format(self._conf.title), 'success')

        return jsonify_data(url=url_for('event_mgmt.conferenceModification', self._conf), flash=False)
