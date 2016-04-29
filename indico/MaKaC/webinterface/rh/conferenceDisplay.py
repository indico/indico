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

import os
import pytz
from datetime import datetime
from flask import Response, flash, request, session
from werkzeug.exceptions import Forbidden

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.rh.conferenceBase as conferenceBase
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.user as user
import MaKaC.webinterface.mail as mail
from MaKaC.webinterface.pages.errors import WPError404
from indico.core.config import Config
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
from MaKaC.errors import MaKaCError, NotFoundError
from MaKaC.PDFinterface.conference import AbstractBook
import zipfile
from cStringIO import StringIO
from MaKaC.i18n import _

import MaKaC.common.timezoneUtils as timezoneUtils
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename

from indico.core import signals
from indico.modules.events.layout import theme_settings
from indico.modules.events.layout.views import WPPage
from indico.modules.events.legacy import XMLEventSerializer
from indico.util.i18n import set_best_lang
from indico.util.signals import values_from_signal
from indico.web.flask.util import send_file


class RHConferenceAccessKey( conferenceBase.RHConferenceBase ):

    _isMobile = False

    def _checkParams(self, params):
        conferenceBase.RHConferenceBase._checkParams(self, params)
        self._accesskey = params.get("accessKey", "").strip()
        self._doNotSanitizeFields.append("accessKey")

    def _process(self):
        access_keys = session.setdefault("accessKeys", {})
        access_keys[self._conf.getUniqueId()] = self._accesskey
        session.modified = True
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


class RHRelativeEvent(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._which = params['which']

    def _process(self):
        evt = self._conf.getOwner().getRelativeEvent(self._which, conf=self._conf)
        if evt:
            self._redirect(urlHandlers.UHConferenceDisplay.getURL(evt))
        else:
            return WPError404(self, urlHandlers.UHConferenceDisplay.getURL(self._conf)).display()


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
            serializer = XMLEventSerializer(self.event_new, session.user)
            return Response(serializer.serialize_event(), mimetype='text/xml')
        else:
            p = self.render_meeting_page(self._conf, view, self._reqParams.get('fr') == 'no')
            return p.display()


class RHConferenceProgram(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConferenceProgram

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._xs = self._normaliseListParam(params.get("xs", []))

    def _process(self):
        p = conferences.WPConferenceProgram(self, self._target)
        return p.display(xs=self._xs)


class RHConferenceProgramPDF(RHConferenceBaseDisplay):

    def _process(self):
        set_best_lang()  # prevents from having a _LazyString when generating a pdf without session.lang set
        tz = timezoneUtils.DisplayTZ(self._aw, self._target).getDisplayTZ()
        filename = "%s - Programme.pdf" % self._target.getTitle()
        from MaKaC.PDFinterface.conference import ProgrammeToPDF
        pdf = ProgrammeToPDF(self._target, tz=tz)
        return send_file(filename, StringIO(pdf.getPDFBin()), 'PDF')


class RHMyStuff(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuff

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p=conferences.WPMyStuff(self,self._target)
        return p.display()


class RHConfMyStuffMyTracks(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuffMyTracks

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        ltracks = self._target.getCoordinatedTracks(self._aw.getUser())

        if len(ltracks) == 1:
            self._redirect(urlHandlers.UHTrackModifAbstracts.getURL(ltracks[0]))
        else:
            p = conferences.WPConfMyStuffMyTracks(self, self._target)
            return p.display()


class RHAbstractBook(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConfAbstractBook

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._noCache = params.get('cache') == '0'

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if not self._conf.getAbstractMgr().isActive() or not self._conf.hasEnabledSection("cfa"):
            raise MaKaCError( _("The Call For Abstracts was disabled by the conference managers"))

    def _getCacheFileName(self):
        dir = os.path.join(Config().getInstance().getXMLCacheDir(), "abstract_books")
        if not os.path.exists(dir):
            os.makedirs(dir)
        return os.path.join(dir, '%s.pdf' % self._conf.getId())

    def _process(self):
        boaConfig = self._conf.getBOAConfig()
        pdfFilename = "%s - Book of abstracts.pdf" % cleanHTMLHeaderFilename(self._target.getTitle())
        cacheFile = self._getCacheFileName()
        if os.path.isfile(cacheFile):
            mtime = pytz.utc.localize(datetime.utcfromtimestamp(os.path.getmtime(cacheFile)))
        else:
            mtime = None

        if boaConfig.isCacheEnabled() and not self._noCache and mtime and mtime > boaConfig.lastChanged:
            return send_file(pdfFilename, cacheFile, 'PDF')
        else:
            tz = timezoneUtils.DisplayTZ(self._aw, self._target).getDisplayTZ()
            pdf = AbstractBook(self._target, self.getAW(), tz=tz)
            fname = pdf.generate()

            with open(fname, 'rb') as f:
                data = f.read()
            with open(cacheFile, 'wb') as f:
                f.write(data)

            return send_file(pdfFilename, cacheFile, 'PDF')


class RHConferenceToXML(RHConferenceBaseDisplay):

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._xmltype = params.get("xmltype","standard")

    def _process(self):
        filename = "%s - Event.xml" % self._target.getTitle()
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("event")
        outgen.confToXML(self._target.getConference(),0,0,1)
        xmlgen.closeTag("event")
        return send_file(filename, StringIO(xmlgen.getXml()), 'XML')


class RHConferenceToMarcXML(RHConferenceBaseDisplay):

    def _process( self ):
        filename = "%s - Event.xml"%cleanHTMLHeaderFilename(self._target.getTitle())
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        outgen.confToXMLMarc21(self._target.getConference())
        xmlgen.closeTag("marc:record")
        return send_file(filename, StringIO(xmlgen.getXml()), 'XML')


class RHConferenceLatexPackage(RHConferenceBaseDisplay):

    def _process(self):
        filename = "%s-BookOfAbstracts.zip" % self._target.getTitle()
        zipdata = StringIO()
        zip = zipfile.ZipFile(zipdata, "w")
        for cont in self._target.as_event.contributions:
            f = []
            f.append("""\\section*{%s}""" % cont.title)
            f.append(" ")
            l = []
            affil = {}
            i = 1
            for pa in cont.primary_authors:
                if pa.affiliation in affil.keys():
                    num = affil[pa.affiliation]
                else:
                    affil[pa.affiliation] = i
                    num = i
                    i += 1

                l.append("""\\noindent \\underline{%s}$^%d$""" % (pa.full_name, num))

            for ca in cont.secondary_authors:
                if ca.affiliation in affil.keys():
                    num = affil[ca.affiliation]
                else:
                    affil[ca.affiliation] = i
                    num = i
                    i += 1
                l.append("""%s$^%d$""" % (ca.full_name, num))

            f.append(",\n".join(l))
            f.append("\n")
            l = []
            for key in affil.keys():
                l.append("""$^%d$%s""" % (affil[key], key))
            f.append("\\noindent " + ",\n".join(l))
            f.append("\n")
            f.append("""\\noindent %s""" % cont.description)
            zip.writestr("contribution-%s" % cont.id, "\n".join(f))
        zip.close()
        zipdata.seek(0)

        return send_file(filename, zipdata, 'ZIP', inline=False)
