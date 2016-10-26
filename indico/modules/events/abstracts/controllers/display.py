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

from operator import attrgetter

from flask import session
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.controllers.base import AbstractPageMixin
from indico.modules.events.abstracts.util import get_user_abstracts
from indico.modules.events.abstracts.views import WPDisplayAbstracts, WPMyAbstracts
from indico.util.fs import secure_filename
from indico.web.flask.util import send_file
from MaKaC.PDFinterface.conference import AbstractToPDF, AbstractsToPDF
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHDisplayAbstract(AbstractPageMixin, RHConferenceBaseDisplay):
    management = False
    page_class = WPDisplayAbstracts

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        AbstractPageMixin._checkParams(self)

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        AbstractPageMixin._checkProtection(self)


class RHDisplayAbstractExportPDF(RHDisplayAbstract):
    def _process(self):
        pdf = AbstractToPDF(self.abstract)
        file_name = secure_filename('abstract-{}.pdf'.format(self.abstract.friendly_id), 'abstract.pdf')
        return send_file(file_name, pdf.generate(), 'application/pdf')


class RHMyAbstractsBase(RHConferenceBaseDisplay):
    """Base RH concerning the list of current user abstracts"""

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.abstracts = get_user_abstracts(self.event_new, session.user)

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if not session.user:
            raise Forbidden


class RHMyAbstracts(RHMyAbstractsBase):
    """Display the list of current user abstracts"""

    def _process(self):
        return WPMyAbstracts.render_template('display/user_abstract_list.html', self._conf, event=self.event_new,
                                             abstracts=self.abstracts)


class RHMyAbstractsExportPDF(RHMyAbstractsBase):
    def _process(self):
        sorted_abstracts = sorted(self.abstracts, key=attrgetter('friendly_id'))
        pdf = AbstractsToPDF(self.event_new, sorted_abstracts)
        return send_file('my-abstracts.pdf', pdf.generate(), 'application/pdf')
