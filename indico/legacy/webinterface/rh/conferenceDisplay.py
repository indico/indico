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

from cStringIO import StringIO

from flask import flash, redirect, request, session
from werkzeug.exceptions import Forbidden

from indico.legacy.webinterface.rh.base import RHDisplayBaseProtected
from indico.legacy.webinterface.rh.conferenceBase import RHConferenceBase
from indico.util.i18n import _
from indico.web.flask.util import send_file


class RHConferenceAccessKey(RHConferenceBase):
    NOT_SANITIZED_FIELDS = {'accessKey'}

    def _process_args(self):
        RHConferenceBase._process_args(self)
        self._accesskey = request.form.get('accessKey', '').strip()

    def _process(self):
        # XXX: we don't check if it's valid or not -- WPKeyAccessError shows a message
        # for that if there's an access key for the event in the session.
        # this is pretty awful but eventually we'll do this properly :)
        self.event.set_session_access_key(self._accesskey)
        return redirect(self.event.url)


class RHConferenceBaseDisplay(RHConferenceBase, RHDisplayBaseProtected):
    def _forbidden_if_not_admin(self):
        if not request.is_xhr and session.user and session.user.is_admin:
            flash(_('This page is currently not visible by non-admin users (menu entry disabled)!'), 'warning')
        else:
            raise Forbidden

    def _process_args(self):
        RHConferenceBase._process_args(self)

    def _check_access(self):
        RHDisplayBaseProtected._check_access(self)


class RHConferenceToMarcXML(RHConferenceBaseDisplay):
    def _process(self):
        from indico.legacy.common.xmlGen import XMLGen
        from indico.legacy.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(session.user, xmlgen)
        xmlgen.openTag(b'marc:record', [
            [b'xmlns:marc', b'http://www.loc.gov/MARC21/slim'],
            [b'xmlns:xsi', b'http://www.w3.org/2001/XMLSchema-instance'],
            [b'xsi:schemaLocation',
             b'http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd']])
        outgen.confToXMLMarc21(self._conf)
        xmlgen.closeTag(b'marc:record')
        return send_file('event-{}.marc.xml'.format(self.event.id), StringIO(xmlgen.getXml()), 'application/xml')
