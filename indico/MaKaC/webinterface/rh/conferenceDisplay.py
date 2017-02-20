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

from cStringIO import StringIO

from flask import Response, flash, request, session
from werkzeug.exceptions import Forbidden

from indico.core import signals
from indico.modules.events.layout import theme_settings
from indico.modules.events.layout.views import WPPage
from indico.modules.events.legacy import XMLEventSerializer
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.web.flask.util import send_file
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename
from MaKaC.webinterface.pages import conferences
from MaKaC.webinterface.rh import base, conferenceBase
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase


class RHConferenceAccessKey( conferenceBase.RHConferenceBase ):

    _isMobile = False

    def _checkParams(self, params):
        conferenceBase.RHConferenceBase._checkParams(self, params)
        self._accesskey = params.get("accessKey", "").strip()
        self._doNotSanitizeFields.append("accessKey")

    def _process(self):
        # XXX: we don't check if it's valid or not -- WPKeyAccessError shows a message
        # for that if there's an access key for the event in the session.
        # this is pretty awful but eventually we'll do this properly :)
        self.event_new.set_session_access_key(self._accesskey)
        url = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        self._redirect(url)


class RHConferenceBaseDisplay( RHConferenceBase, RHDisplayBaseProtected ):

    def _forbidden_if_not_admin(self):
        if not request.is_xhr and session.user and session.user.is_admin:
            flash(_('This page is currently not visible by non-admin users (menu entry disabled)!'), 'warning')
        else:
            raise Forbidden

    def _checkParams( self, params ):
        RHConferenceBase._checkParams( self, params )

    def _checkProtection(self):
        RHDisplayBaseProtected._checkProtection(self)


class MeetingRendererMixin:
    def render_meeting_page(self, conf, view, hide_frame=False):
        evt_type = conf.getType()
        view = view or conf.as_event.theme

        # if the current view is invalid, use the default
        if view not in theme_settings.themes:
            view = theme_settings.defaults[evt_type]

        if view in theme_settings.xml_themes:
            if hide_frame:
                self._responseUtil.content_type = 'text/xml'
            return conferences.WPXSLConferenceDisplay(self, conf, view, evt_type, self._reqParams)
        elif view == "static":
            return conferences.WPConferenceDisplay(self, conf)
        else:
            return conferences.WPTPLConferenceDisplay(self, conf, view, evt_type, self._reqParams)


class RHConferenceDisplay(MeetingRendererMixin, RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConferenceDisplay

    def _checkProtection(self):
        # check users allowed by plugins
        if any(values_from_signal(signals.event.has_read_access.send(self._conf, user=session.user))):
            return
        RHConferenceBaseDisplay._checkProtection(self)

    def _process( self ):
        params = self._getRequestParams()
        if not self._reqParams.has_key("showDate"):
            self._reqParams["showDate"] = "all"
        if not self._reqParams.has_key("showSession"):
            self._reqParams["showSession"] = "all"
        if not self._reqParams.has_key("detailLevel"):
            self._reqParams["detailLevel"] = "contribution"

        warningText = ""

        # create the html factory
        if self._target.getType() == "conference":
            if params.get("ovw", False):
                p = conferences.WPConferenceDisplay( self, self._target )
            else:
                event = self._conf.as_event
                if event.default_page_id is None:
                    p = conferences.WPConferenceDisplay(self, self._conf)
                else:
                    p = WPPage.render_template('page.html', self._conf, page=event.default_page)
        else:
            p = self.render_meeting_page(self._conf, self._reqParams.get("view"), self._reqParams.get('fr') == 'no')

        return warningText + (p if isinstance(p, basestring) else p.display(**params))


class RHConferenceOtherViews(MeetingRendererMixin, RHConferenceBaseDisplay):
    """
    this class is for the conference type objects only
    it is an alternative to the standard TimeTable view
    """
    _uh = urlHandlers.UHConferenceOtherViews

    def _process( self ):
        if not self._reqParams.has_key("showDate"):
            self._reqParams["showDate"] = "all"
        if not self._reqParams.has_key("showSession"):
            self._reqParams["showSession"] = "all"
        if not self._reqParams.has_key("detailLevel"):
            self._reqParams["detailLevel"] = "contribution"

        view = self._reqParams.get('view')
        if view == 'xml':
            serializer = XMLEventSerializer(self.event_new, user=session.user, include_timetable=True,
                                            event_tag_name='iconf')
            return Response(serializer.serialize_event(), mimetype='text/xml')
        else:
            p = self.render_meeting_page(self._conf, view, self._reqParams.get('fr') == 'no')
            return p.display()


class RHMyStuff(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuff

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p=conferences.WPMyStuff(self,self._target)
        return p.display()


class RHConferenceToXML(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)

    def _process(self):
        filename = u'event-{}.xml'.format(self.event_new.id)
        serializer = XMLEventSerializer(self.event_new, user=session.user, include_announcer_email=True)
        return send_file(filename, StringIO(serializer.serialize_event()), 'XML')


class RHConferenceToMarcXML(RHConferenceBaseDisplay):

    def _process( self ):
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        outgen.confToXMLMarc21(self._target.getConference())
        xmlgen.closeTag("marc:record")
        return send_file(u'event-{}.marc.xml'.format(self.event_new.id), StringIO(xmlgen.getXml()), 'XML')
