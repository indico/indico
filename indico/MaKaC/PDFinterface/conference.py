# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.
from MaKaC.common import logger, utils
import string
import types
from copy import deepcopy
from textwrap import wrap, fill
from PIL import Image
from qrcode import QRCode, constants

from MaKaC.PDFinterface.base import escape, Int2Romans
from datetime import timedelta,datetime
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.rl_config import defaultPageSize
from reportlab.platypus import Table,TableStyle,KeepTogether, XPreformatted
from reportlab.pdfgen import canvas
from MaKaC.common.timezoneUtils import DisplayTZ,nowutc
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.review as review
import MaKaC.conference as conference
import MaKaC.schedule as schedule
from MaKaC.badge import BadgeTemplateItem
from MaKaC.poster import PosterTemplateItem
from MaKaC.registration import Registrant
from MaKaC.PDFinterface.base import PDFBase, PDFWithTOC, Paragraph, Spacer, PageBreak, Preformatted, FileDummy, setTTFonts, PDFSizes, modifiedFontSize, SimpleParagraph
from MaKaC.webinterface.pages.tracks import AbstractStatusTrackViewFactory, _ASTrackViewPFOT, _ASTrackViewPA, _ASTrackViewDuplicated, _ASTrackViewMerged,_ASTrackViewAccepted, _ASTrackViewIC
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.errors import MaKaCError, NoReportError
from MaKaC.webinterface.common.countries import CountryHolder
from reportlab.lib.pagesizes import landscape, A4
from MaKaC.badgeDesignConf import BadgeDesignConfiguration
from MaKaC.posterDesignConf import PosterDesignConfiguration
from MaKaC.webinterface.common.tools import strip_ml_tags
import re
from MaKaC.i18n import _
from indico.util.i18n import i18nformat, ngettext
from indico.util.date_time import format_date
from indico.util import json
from MaKaC.common.Configuration import Config


styles = getSampleStyleSheet()
charRplace = [
[u'\u2019', u"'"],
[u'\u0153', u"oe"],
[u'\u2026', u"..."],
[u'\u2013', u"-"],
[u'\u2018', u"'"]
]



class ProgrammeToPDF(PDFBase):

    def __init__(self, conf, doc=None, story=None, tz=None):
        self._conf = conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        PDFBase.__init__(self, doc, story)
        self._title = _("Conference Scientific Programme")

    def firstPage(self, c, doc):
        c.saveState()

        height = self._drawLogo(c)

        if not height:
            height = self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)

        c.setFont('Times-Bold', 15)

        height -= 2 * cm;

        c.drawCentredString(self._PAGE_WIDTH/2.0, height, "%s - %s"%(self._conf.getAdjustedStartDate(self._tz).strftime("%A %d %B %Y"), self._conf.getAdjustedEndDate(self._tz).strftime("%A %d %B %Y")))
        if self._conf.getLocation():
            height-=1*cm
            c.drawCentredString(self._PAGE_WIDTH/2.0, height, escape(self._conf.getLocation().getName()))
        c.setFont('Times-Bold', 30)
        height-=6*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0, height, self._title)
        self._drawWrappedString(c, "%s / %s"%(strip_ml_tags(self._conf.getTitle()),self._title), width=inch, height=0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        self._drawWrappedString(c, "%s / %s"%(escape(strip_ml_tags(self._conf.getTitle())),self._title), width=inch, height=self._PAGE_HEIGHT-0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
        c.drawCentredString(self._PAGE_WIDTH/2.0, 0.75 * inch, "Page %d "%doc.page)
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def getBody(self, story=None):
        if not story:
            story = self._story
        style = styles["Normal"]
        style.alignment = TA_JUSTIFY
        p = Paragraph(escape(self._conf.getProgramDescription()), style)
        story.append(p)
        story.append(Spacer(1, 0.4*inch))

        for track in self._conf.getTrackList():

            bogustext = track.getTitle()
            p = Paragraph(escape(bogustext), styles["Heading1"])
            self._story.append(p)
            bogustext = track.getDescription()
            p = Paragraph(escape(bogustext), style)
            story.append(p)
            story.append(Spacer(1, 0.4*inch))



class AbstractToPDF(PDFBase):

    def __init__(self, conf, abstract, doc=None, story=None, tz=None):
        self._conf = conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._abstract = abstract
        if not story:
            story = [Spacer(inch, 5*cm)]
        PDFBase.__init__(self, doc, story)
        self._title = _("Abstract")
        self._PAGE_HEIGHT = defaultPageSize[1]
        self._PAGE_WIDTH = defaultPageSize[0]

    def firstPage(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)

        c.setFont('Times-Bold', 25)
        #c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT - inch - 5*cm, self._abstract.getTitle())
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        #c.drawString(0.5*inch, 0.5*inch, Config.getInstance().getBaseURL())
        c.restoreState()

    def _getTrackText(self):
        text = i18nformat("""_("Track classification") : """)
        status=self._abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusAccepted):
            if status.getTrack() is not None:
                text="%s%s"%(text,escape(status.getTrack().getTitle()))
        else:
            listTrack= []
            for track in self._abstract.getTrackListSorted():
                listTrack.append( escape(track.getTitle()))
            text += " ; ".join(listTrack)
        return text

    def _getContribTypeText(self):
        status=self._abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusAccepted):
            text= i18nformat(""" _("Contribution type") : %s""")%(escape(str(status.getType())))
        else:
            text= i18nformat(""" _("Contribution type") : %s""")%escape(str(self._abstract.getContribType()))
        return text

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story

        #style = ParagraphStyle({})
        #style.fontSize = 12
        text = i18nformat(""" _("Abstract ID"): %s""") % self._abstract.getId()
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text, 12)
        story.append(p)

        story.append(Spacer(inch, 0.5*cm, part=escape(self._abstract.getTitle())))

        style = ParagraphStyle({})
        style.alignment = TA_CENTER
        style.fontSize = 25
        style.leading = 30
        text = escape(self._abstract.getTitle())
        p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        story.append(p)

        flowableText = escape(self._abstract.getTitle())
        if self._conf.getBOAConfig().getShowIds():
            flowableText += """ (%s)"""%self._abstract.getId()
        indexedFlowable[p] = {"text":escape(flowableText), "level":1}

        style = ParagraphStyle({})
        style.fontName = "LinuxLibertine"
        style.fontSize = 9
        style.alignment = TA_JUSTIFY
        #XXX:Not optimal, but the only way I've found to do it
        #l=self._abstract.getField("content").split("\n")
        #res=[]
        #for line in l:
        #    res.append(fill(line,85))
        #res="\n".join(res)
        #p = Preformatted(escape(res), style, part=escape(self._abstract.getTitle()))
        #story.append(p)

        story.append(Spacer(inch, 0.5*cm, part=escape(self._abstract.getTitle())))

        for field in self._conf.getAbstractMgr().getAbstractFieldsMgr().getActiveFields():
            fid = field.getId()
            name = field.getCaption()
            value = str(self._abstract.getField(fid)).strip()
            if value:  # id not in ["content"] and
                if fid != "content" and fid != "summary":
                    text = "%s: %s" % (name, value)
                    p = SimpleParagraph(text, spaceAfter=5)
                    story.append(p)
                else:
                    text = "%s:" % name
                    p = SimpleParagraph(text, spaceAfter=5)
                    story.append(p)
                    p = Paragraph(escape(value), style, part=escape(self._abstract.getTitle()))
                    story.append(p)

                story.append(Spacer(inch, 0.2*cm, part=escape(self._abstract.getTitle())))

        story.append(Spacer(inch, 0.5*cm, part=escape(self._abstract.getTitle())))
        style = ParagraphStyle({})
        style.firstLineIndent = -80
        style.leftIndent = 80
        style.alignment = TA_JUSTIFY
        text = i18nformat("""<b> _("Primary authors")</b>: """)
        listAuthor = []
        for author in self._abstract.getPrimaryAuthorsList():
            listAuthor.append( "%s (%s)"%(escape(author.getFullName()), escape(author.getAffiliation()))  )
        text += " ; ".join(listAuthor)
        p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        story.append(p)

        story.append(Spacer(inch, 0.2*cm))

        style = ParagraphStyle({})
        style.firstLineIndent = -35
        style.leftIndent = 35
        style.alignment = TA_JUSTIFY
        text = i18nformat("""<b> _("Co-authors")</b>: """)
        listAuthor = []
        for author in self._abstract.getCoAuthorList():
            listAuthor.append( "%s (%s)"%(escape(author.getFullName()), escape(author.getAffiliation()) )  )
        text += " ; ".join(listAuthor)

        p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._abstract.getTitle())))

        #style = ParagraphStyle({})
        #style.firstLineIndent = -45
        #style.leftIndent = 45
        text = i18nformat("""_("Presenter"): """)
        listSpeaker= []
        for speaker in self._abstract.getSpeakerList():
            listSpeaker.append( "%s (%s)"%(escape(speaker.getFullName()), escape(speaker.getAffiliation()) )  )
        text += " ; ".join(listSpeaker)
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text)
        story.append(p)

        story.append(Spacer(inch, 0.5*cm, part=escape(self._abstract.getTitle())))
        style = ParagraphStyle({})
        style.firstLineIndent = -90
        style.leftIndent = 90
        p = Paragraph(self._getTrackText(), style, part=escape(self._abstract.getTitle()))
        #p = SimpleParagraph(self._getTrackText())
        story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._abstract.getTitle())))
        tmp= i18nformat("""--_("not specified")--""")
        if self._abstract.getContribType() is not None:
            tmp=self._abstract.getContribType().getName()
        text = i18nformat("""_("Contribution type"): %s""")%escape(tmp)
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text)
        story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._abstract.getTitle())))

        text = i18nformat("""_("Submitted by"): %s""")%escape(self._abstract.getSubmitter().getFullName())
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text)
        story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._abstract.getTitle())))

        text = i18nformat("""_("Submitted on") %s""")%self._abstract.getSubmissionDate().strftime("%A %d %B %Y")
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text)
        story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._abstract.getTitle())))

        text = i18nformat("""_("Last modified on"): %s""")%self._abstract.getModificationDate().strftime("%A %d %B %Y")
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text)
        story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._abstract.getTitle())))

        text = i18nformat("""_("Comments"): """)
        p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        #p = SimpleParagraph(text)
        story.append(p)

        style = ParagraphStyle({})
        style.leftIndent = 40
        style.alignment = TA_JUSTIFY
        text = "%s"%escape(self._abstract.getComments())
        p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        story.append(p)

        return story


class AbstractsToPDF(PDFWithTOC):

    def __init__(self, conf, abstractList, tz=None):
        self._conf = conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._abstracts = abstractList
        self._title = _("Abstracts book")
        PDFWithTOC.__init__(self)

    def firstPage(self, c, doc):
        c.saveState()
        showLogo = False
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)

        c.setFont('Times-Bold', 35)
        c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT/2, self._title)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        c.setFont('Times-Roman', 10)
        c.drawString(0.5*inch, 0.5*inch, str(urlHandlers.UHConferenceDisplay.getURL(self._conf)))
        c.restoreState()

    def laterPages(self, c, doc):

        c.saveState()
        c.setFont('Times-Roman', 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        confTitle = escape(self._conf.getTitle())
        if len(self._conf.getTitle())>30:
            confTitle = escape(self._conf.getTitle()[:30] + "...")
        c.drawString(inch, self._PAGE_HEIGHT - 0.75 * inch, "%s / %s"%(confTitle, self._title))
        title = doc.getCurrentPart()
        if len(doc.getCurrentPart())>50:
            title = utils.unicodeSlice(doc.getCurrentPart(), 0, 50) + "..."
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, "%s"%title)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, i18nformat(""" _("Page") %d """)%doc.page)
        c.drawString(inch,  0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()


    def getBody(self):
        abMgr = self._conf.getAbstractMgr()
        for abstract in self._abstracts:
            temp = AbstractToPDF(self._conf, abMgr.getAbstractById(abstract), tz=self._tz)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())


class ConfManagerAbstractToPDF(AbstractToPDF):

    def _getTrackText(self):
        text = i18nformat("""_("Track classification") : """)
        listTrack= []
        for track in self._abstract.getTrackListSorted():
            listTrack.append( escape(track.getTitle()))
        text += " ; ".join(listTrack)
        return text

    def _getContribTypeText(self):
        status=self._abstract.getCurrentStatus()
        text= i18nformat("""_("Contribution type") : %s""")%escape(str(self._abstract.getContribType()))
        return text

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story
        #get the common abstract content from parent
        AbstractToPDF.getBody(self, story, indexedFlowable, level )
        #add info for the conference manager
        story.append(Spacer(inch, 0.5*cm, part=escape(self._abstract.getTitle())))
        status = self._abstract.getCurrentStatus()
        #style = ParagraphStyle({})
        #style.firstLineIndent = -90
        #style.leftIndent = 90
        if status.__class__ == review.AbstractStatusDuplicated:
            original=status.getOriginal()
            st = i18nformat(""" _("DUPLICATED") (%s: %s)""")%(original.getId(), original.getTitle())
        elif status.__class__ == review.AbstractStatusMerged:
            target=status.getTargetAbstract()
            st = i18nformat(""" _("MERGED") (%s: %s)""")%(target.getId(), target.getTitle())
        else:
            st = AbstractStatusList.getInstance().getCaption( status.__class__ ).upper()
        text = i18nformat("""_("Status"): %s""")%escape(st)
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text)
        story.append(p)
        story.append(Spacer(inch, 0.5*cm, part=escape(self._abstract.getTitle())))
        #style = ParagraphStyle({})
        #style.firstLineIndent = -90
        #style.leftIndent = 90
        text = i18nformat("""_("Track judgments"):""")
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text)
        story.append(p)

        for track in self._abstract.getTrackListSorted():
            status = self._abstract.getTrackJudgement(track)
            if status.__class__ == review.AbstractAcceptance:
                contribType = ""
                if status.getContribType() is not None:
                    contribType = "(%s)"%status.getContribType().getName()
                st = i18nformat(""" _("Proposed to accept") %s""")%(contribType)
            elif status.__class__ == review.AbstractRejection:
                st = _("Proposed to reject")
            elif status.__class__ == review.AbstractInConflict:
                st = _("Conflict")
            elif status.__class__ == review.AbstractReallocation:
                l = []
                for track in status.getProposedTrackList():
                    l.append( track.getTitle() )
                st = i18nformat(""" _("Proposed for other tracks") (%s)""")%", ".join(l)
            else:
                st = ""

            story.append(Spacer(inch, 0.5*cm, part=escape(self._abstract.getTitle())))

            status = self._abstract.getCurrentStatus()
            #style = ParagraphStyle({})
            #style.firstLineIndent = -90
            #style.leftIndent = 130
            text = i18nformat("""_("Track") : %s""")%escape(track.getTitle())
            #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
            p = SimpleParagraph(text, indent = 40)
            story.append(p)

            story.append(Spacer(inch, 0.1*cm, part=escape(self._abstract.getTitle())))

            status = self._abstract.getCurrentStatus()
            #style = ParagraphStyle({})
            #style.firstLineIndent = -90
            #style.leftIndent = 170
            text = i18nformat("""_("Judgment") : %s""")%st
            #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
            p = SimpleParagraph(text, indent = 80)
            story.append(p)

class ConfManagerAbstractsToPDF(AbstractsToPDF):

    def getBody(self):
        abMgr = self._conf.getAbstractMgr()
        for abstract in self._abstracts:
            temp = ConfManagerAbstractToPDF(self._conf, abMgr.getAbstractById(abstract),tz=self._tz)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())


class TrackManagerAbstractToPDF(AbstractToPDF):

    def __init__(self, conf, abstract, track, doc=None, story=None, tz=None):
        AbstractToPDF.__init__(self, conf, abstract, doc, story, tz=tz)
        self._track = track
#        self._tz = tz

    def _getTrackText(self):
        text = i18nformat("""<b> _("Track classification")</b>: """)
        listTrack= []
        for track in self._abstract.getTrackListSorted():
            listTrack.append( escape(track.getTitle()))
        text += " ; ".join(listTrack)
        return text

    def _getContribTypeText(self):
        status=self._abstract.getCurrentStatus()
        text= i18nformat("""<b> _("Contribution type")</b>: %s""")%escape(str(self._abstract.getContribType()))
        return text

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story
        #get the common abstract content from parent
        AbstractToPDF.getBody(self, story, indexedFlowable, level )

        #add info for the track manager
        status=AbstractStatusTrackViewFactory.getStatus(self._track,self._abstract)
        comments = escape(status.getComment())
        st = status.getLabel().upper()
        conflictText, res = "", ""
        if isinstance(status, _ASTrackViewPFOT):
            l = []
            for track in status.getProposedTrackList():
                l.append( escape(track.getTitle()) )
            res = "%s"%", ".join(l)
        elif isinstance(status, _ASTrackViewPA):
            contribType = ""
            if status.getContribType() is not None:
                contribType = "(%s)"%status.getContribType().getName()
            res = "%s %s"%( status.getLabel().upper(), \
                              contribType )
            conflicts = status.getConflicts()
            if conflicts:
                l = []
                for jud in conflicts:
                    if jud.getTrack() != self._track:
                        l.append( "%s ( %s )"%( jud.getTrack().getTitle(), \
                                escape(jud.getResponsible().getFullName()) ) )
                conflictText = ",\n".join(l)
        elif isinstance(status, _ASTrackViewIC):
            st = self.htmlText(status.getLabel().upper())
        elif isinstance(status, _ASTrackViewDuplicated):
            orig = status.getOriginal()
            st =  "%s (%s : %s)"%(status.getLabel().upper(), orig.getId(), orig.getTitle())
        elif isinstance(status, _ASTrackViewMerged):
            target=status.getTarget()
            st = "%s (%s : %s)"%(status.getLabel().upper(), target.getId(), target.getTitle())
        elif isinstance(status,_ASTrackViewAccepted):
            if status.getContribType() is not None and \
                                                status.getContribType()!="":
                contribType = ""
                if status.getContribType() is not None:
                    contribType = "(%s)"%status.getContribType().getName()
                st = "%s %s"%(status.getLabel().upper(),contribType)
        story.append(Spacer(inch, 0.5*cm, part=escape(self._abstract.getTitle())))
        status = self._abstract.getCurrentStatus()
        #style = ParagraphStyle({})
        #style.firstLineIndent = -90
        #style.leftIndent = 90
        if st:
            text = i18nformat("""_("Status") : %s""")%st
        else:
            text = i18nformat("""_("Status") : _("SUBMITTED")""")
        #p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
        p = SimpleParagraph(text)
        story.append(p)



        #story.append(Spacer(inch, 0.1*cm, part=self._abstract.getTitle()))

        if res:
            status = self._abstract.getCurrentStatus()
            style = ParagraphStyle({})
            style.leftIndent = 60
            text = "(<i>%s</i>)"%res
            p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
            story.append(p)


        if comments:
            status = self._abstract.getCurrentStatus()
            style = ParagraphStyle({})
            style.leftIndent = 40
            text = "\"<i>%s</i>\""%comments
            p = Paragraph(text, style, part=escape(self._abstract.getTitle()))
            story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._abstract.getTitle())))

        if conflictText:
            style = ParagraphStyle({})
            style.leftIndent = 40
            p = Paragraph( i18nformat(""" _("In conflict with"): """), style, part=escape(self._abstract.getTitle()))
            story.append(p)

            style = ParagraphStyle({})
            style.leftIndent = 60
            p = Preformatted(conflictText, style, part=escape(self._abstract.getTitle()))
            story.append(p)


class TrackManagerAbstractsToPDF(AbstractsToPDF):

    def __init__(self, conf, track, abstractList, tz=None):
        AbstractsToPDF.__init__(self, conf, abstractList, tz)
        self._track = track

    def getBody(self):
        abMgr = self._conf.getAbstractMgr()
        for abstract in self._abstracts:
            temp = TrackManagerAbstractToPDF(self._conf, abMgr.getAbstractById(abstract), self._track, tz=self._tz)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())


class ContribToPDF(PDFBase):

    def __init__(self, conf, contrib, doc=None, story=None, tz=None):
        self._conf = conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._contrib = contrib
        if not story:
            story = [Spacer(inch, 5*cm)]
        PDFBase.__init__(self, doc, story)
        self._title = _("Contribution")
        self._PAGE_HEIGHT = defaultPageSize[1]
        self._PAGE_WIDTH = defaultPageSize[0]

    def firstPage(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 25)
        #c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT - inch - 5*cm, self._abstract.getTitle())
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        #c.drawString(0.5*inch, 0.5*inch, Config.getInstance().getBaseURL())
        c.restoreState()

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story

        style = ParagraphStyle({})
        style.fontSize = 12
        text = i18nformat(""" _("Contribution ID"): %s""")%self._contrib.getId()
        p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
        story.append(p)

        story.append(Spacer(inch, 0.5*cm, part=escape(self._contrib.getTitle())))

        style = ParagraphStyle({})
        style.alignment = TA_CENTER
        style.fontSize = 25
        style.leading = 30
        text = escape(self._contrib.getTitle())
        p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
        story.append(p)

        if self._contrib.isScheduled():
            style = ParagraphStyle({})
            style.alignment = TA_CENTER
            style.fontSize = 12
            style.leading = 30
            text = "%s (%s)" % (escape(self._contrib.getAdjustedStartDate(self._tz).strftime("%A %d %b %Y at %H:%M")),escape((datetime(1900,1,1)+self._contrib.getDuration()).strftime("%Hh%M'")))
            p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
            story.append(p)

        indexedFlowable[p] = {"text":escape(self._contrib.getTitle()), "level":1}

        story.append(Spacer(inch, 1*cm, part=escape(self._contrib.getTitle())))

        style = ParagraphStyle({})
        style.fontName = "LinuxLibertine"
        style.fontSize = 9
        for field in self._conf.getAbstractMgr().getAbstractFieldsMgr().getActiveFields():
            fid = field.getId()
            name = field.getCaption()
            value = str(self._contrib.getField(fid)).strip()
            if value: #id not in ["content"] and
                if isinstance(field, review.AbstractTextAreaField):
                    styleHead = ParagraphStyle({})
                    # styleHead.firstLineIndent = -55
                    # styleHead.leftIndent = 45
                    text = "<b>%s</b>:" % name
                    p = Paragraph(text, styleHead, part=escape(self._contrib.getTitle()))
                    story.append(p)
                    l = value.split("\n")
                    res = []
                    for line in l:
                        res.append(fill(line, 85))
                    res = "\n".join(res)
                    p = Paragraph(escape(res), style, part=escape(self._contrib.getTitle()))
                    story.append(p)
                else:
                    styleHead = ParagraphStyle({})
                    # styleHead.firstLineIndent = -55
                    # styleHead.leftIndent = 45
                    text = "<b>%s</b>: %s" % (name, value)
                    p = Paragraph(text, styleHead, part=escape(self._contrib.getTitle()))
                    story.append(p)
                story.append(Spacer(inch, 0.2*cm, part=escape(self._contrib.getTitle())))


        story.append(Spacer(inch, 0.5*cm, part=escape(self._contrib.getTitle())))

        style = ParagraphStyle({})
        # style.firstLineIndent = -55
        # style.leftIndent = 45
        text = i18nformat("""<b> _("Primary authors")</b>: """)
        listAuthor = []
        for author in self._contrib.getPrimaryAuthorsList():
            listAuthor.append( "%s (%s)"%(escape(author.getFullName()), escape(author.getAffiliation()))  )
        text += " ; ".join(listAuthor)
        p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
        story.append(p)

        story.append(Spacer(inch, 0.2*cm))

        style = ParagraphStyle({})
        style.firstLineIndent = -35
        style.leftIndent = 35
        text = i18nformat("""<b> _("Co-authors")</b>: """)
        listAuthor = []
        for author in self._contrib.getCoAuthorList():
            listAuthor.append( "%s (%s)"%(escape(author.getFullName()), escape(author.getAffiliation()) )  )
        text += " ; ".join(listAuthor)

        p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
        story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._contrib.getTitle())))

        style = ParagraphStyle({})
        style.firstLineIndent = -45
        style.leftIndent = 45
        text = i18nformat("""<b> _("Presenter")</b>: """)
        listSpeaker= []
        for speaker in self._contrib.getSpeakerList():
            listSpeaker.append( "%s (%s)"%(escape(speaker.getFullName()), escape(speaker.getAffiliation()) )  )
        text += " ; ".join(listSpeaker)
        p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
        story.append(p)

        story.append(Spacer(inch, 0.5*cm, part=escape(self._contrib.getTitle())))
        style = ParagraphStyle({})
        style.firstLineIndent = -90
        style.leftIndent = 90
        session = self._contrib.getSession()
        if session!=None:
            sessiontitle = session.getTitle()
        else:
            sessiontitle = i18nformat("""--_("not yet classified")--""")
        text = i18nformat("""<b> _("Session classification")</b>:  %s""")%escape(sessiontitle)
        p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
        story.append(p)

        story.append(Spacer(inch, 0.5*cm, part=escape(self._contrib.getTitle())))

        style = ParagraphStyle({})
        style.firstLineIndent = -90
        style.leftIndent = 90
        track = self._contrib.getTrack()
        if track!=None:
            tracktitle = track.getTitle()
        else:
            tracktitle = i18nformat("""--_("not yet classified")--""")
        text = i18nformat("""<b> _("Track classification")</b>:  %s""")%escape(tracktitle)
        p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
        story.append(p)

        story.append(Spacer(inch, 0.2*cm, part=escape(self._contrib.getTitle())))

        tmp=i18nformat("""--_("not specified")--""")
        if self._contrib.getType():
            tmp=self._contrib.getType().getName()
        text = i18nformat("""<b> _("Type")</b>: %s""")%escape(tmp)
        p = Paragraph(text, style, part=escape(self._contrib.getTitle()))
        story.append(p)

        return story

class ConfManagerContribToPDF(ContribToPDF):

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story

        #get the common contribution content from parent
        ContribToPDF.getBody(self, story, indexedFlowable, level )

        #add info for the conference manager


class ContributionBook(PDFBase):

    def __init__(self,conf,contribList,aw,tz=None, sortedBy=""):
        self._conf=conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._contribList = contribList
        self._aw=aw
        PDFBase.__init__(self)
        self._title=_("Book of abstracts")
        self._sortedBy = sortedBy
        if self._sortedBy == "boardNo":
            try:
                self._contribList = sorted(self._contribList, key=lambda x:int(x.getBoardNumber()))
            except ValueError,e:
                raise MaKaCError(_("In order to generate this PDF, all the contributions must contain a board number and it must only contain digits. There is a least one contribution with a wrong board number."))
        self._doc.leftMargin=1*cm
        self._doc.rightMargin=1*cm
        self._doc.topMargin=1.5*cm
        self._doc.bottomMargin=1*cm

    def firstPage(self,c,doc):
        c.saveState()
        self._drawLogo(c, False)
        height=self._drawWrappedString(c, self._conf.getTitle())
        c.setFont('Times-Bold',15)
        height-=2*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0,height,
                "%s - %s"%(self._conf.getAdjustedStartDate(self._tz).strftime("%A %d %B %Y"),
                self._conf.getAdjustedEndDate(self._tz).strftime("%A %d %B %Y")))
        if self._conf.getLocation():
            height-=1*cm
            c.drawCentredString(self._PAGE_WIDTH/2.0,height,
                    escape(self._conf.getLocation().getName()))
        c.setFont('Times-Bold', 30)
        height-=6*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0,height,\
                self._title)
        self._drawWrappedString(c, "%s / %s"%(self._conf.getTitle(),self._title), width=inch, height=0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
        c.drawRightString(self._PAGE_WIDTH-inch,0.75*inch,
                nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def laterPages(self,c,doc):
        c.saveState()
        c.setFont('Times-Roman',9)
        c.setFillColorRGB(0.5,0.5,0.5)
        c.drawString(1*cm,self._PAGE_HEIGHT-1*cm,
            "%s / %s"%(escape(self._conf.getTitle()),self._title))
        c.drawCentredString(self._PAGE_WIDTH/2.0,0.5*cm,"Page %d "%doc.page)
        c.restoreState()

    def _defineStyles(self):
        self._styles={}
        titleStyle=getSampleStyleSheet()["Heading1"]
        titleStyle.fontSize=13.0
        titleStyle.spaceBefore=0
        titleStyle.spaceAfter=4
        titleStyle.leading=14
        self._styles["title"]=titleStyle
        spkStyle=getSampleStyleSheet()["Heading2"]
        spkStyle.fontSize=10.0
        spkStyle.spaceBefore=0
        spkStyle.spaceAfter=0
        spkStyle.leading=14
        self._styles["speakers"]=spkStyle
        abstractStyle=getSampleStyleSheet()["Normal"]
        abstractStyle.fontSize=10.0
        abstractStyle.spaceBefore=0
        abstractStyle.spaceAfter=0
        abstractStyle.alignment=TA_LEFT
        self._styles["abstract"]=abstractStyle
        ttInfoStyle=getSampleStyleSheet()["Normal"]
        ttInfoStyle.fontSize=10.0
        ttInfoStyle.spaceBefore=0
        ttInfoStyle.spaceAfter=0
        self._styles["tt_info"]=ttInfoStyle
        normalStyle=getSampleStyleSheet()["Normal"]
        normalStyle.fontSize=10.0
        normalStyle.spaceBefore=5
        normalStyle.spaceAfter=5
        normalStyle.alignment=TA_LEFT
        self._styles["normal"]=normalStyle

    def getBody(self,story=None):
        self._defineStyles()
        if not story:
            story=self._story
        story.append(PageBreak())
        if self._conf.getBOAConfig().getText() != "":
            text=self._conf.getBOAConfig().getText().replace("<BR>","<br>")
            text=text.replace("<Br>","<br>")
            text=text.replace("<bR>","<br>")
            for par in text.split("<br>"):
                p=Paragraph(par,self._styles["normal"])
                story.append(p)
            story.append(PageBreak())
        for contrib in self._contribList:
            if not contrib.canAccess(self._aw):
                continue
            if self._sortedBy == "boardNo":
                caption="%s"%(contrib.getTitle())
            else:
                caption="%s - %s"%(contrib.getId(),contrib.getTitle())
            p1=Paragraph(escape(caption),self._styles["title"])
            lspk=[]
            for spk in contrib.getSpeakerList():
                fullName=spk.getFullName()
                instit=spk.getAffiliation().strip()
                if instit!="":
                    fullName="%s (%s)"%(fullName, instit)
                lspk.append("%s"%escape(fullName))
            speakers= i18nformat("""<b>_("Presenter"): %s</b>""")%"; ".join(lspk)
            p2=Paragraph(speakers,self._styles["speakers"])
            abstract = contrib.getDescription()
            p3=Paragraph(escape(abstract),self._styles["abstract"])
            ses=""
            if contrib.getSession() is not None:
                ses=contrib.getSession().getTitle()
            if contrib.getBoardNumber():
                if ses != "":
                    ses = "%s - "%ses
                ses="%sBoard: %s"%(ses, contrib.getBoardNumber())
            if contrib.isScheduled():
                if ses != "":
                    ses = "%s - "%ses
                text="%s%s"%(ses,contrib.getAdjustedStartDate(self._tz).strftime("%A %d %B %Y %H:%M"))
            else:
                text = ses
            p4=Paragraph(escape(text),self._styles["tt_info"])
            abs=KeepTogether([p1,p4,p2,p3])
            story.append(abs)
            story.append(Spacer(1,0.4*inch))


class ContribsToPDF(PDFWithTOC):

    def __init__(self, conf, contribList, tz=None):
        self._conf = conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._contribs = contribList
        self._title = _("Contributions book")
        PDFWithTOC.__init__(self)

    def firstPage(self, c, doc):
        c.saveState()
        showLogo = False
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 35)
        c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT/2, self._title)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        c.drawString(0.5*inch, 0.5*inch, str(urlHandlers.UHConferenceDisplay.getURL(self._conf)))
        c.restoreState()

    def laterPages(self, c, doc):

        c.saveState()
        c.setFont('Times-Roman', 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        confTitle = escape(self._conf.getTitle())
        if len(self._conf.getTitle())>30:
            confTitle = escape(self._conf.getTitle()[:30] + "...")
        c.drawString(inch, self._PAGE_HEIGHT - 0.75 * inch, "%s / %s"%(confTitle, self._title))
        title = doc.getCurrentPart()
        if len(doc.getCurrentPart())>50:
            title = utils.unicodeSlice(doc.getCurrentPart(), 0, 50) + "..."
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, "%s"%title)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, i18nformat(""" _("Page") %d """)%doc.page)
        c.drawString(inch,  0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()


    def getBody(self):
        for contrib in self._contribs:
            temp = ContribToPDF(self._conf, contrib, tz=self._tz)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())

class ConfManagerContribsToPDF(ContribsToPDF):

    def getBody(self):
        for contrib in self._contribs:
            temp = ConfManagerContribToPDF(self._conf, contrib,tz=self._tz)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())

class TimetablePDFFormat:

    def __init__(self, params=None):
        if params is None:
            self.contribId = True
            self.speakerTitle = True
            self.contribAbstract = False
            self.newPagePerSession = False
            self.useSessionColorCodes = False
            self.showSessionTOC = False
            self.logo = False
            self.lengthContribs = False
            self.contribsAtConfLevel=False
            self.breaksAtConfLevel=False
            self.dateCloseToSessions=False
            self.coverPage=True
            self.tableContents=True
        else:
            self.setValues(params)

    def setValues(self, params):
        self.contribId = True
        if not params.has_key("showContribId"):
            self.contribId = False

        self.speakerTitle = True
        if not params.has_key("showSpeakerTitle"):
            self.speakerTitle = False

        self.contribAbstract = False
        if params.has_key("showAbstract"):
            self.contribAbstract = True

        self.contribPosterAbstract = True
        if params.has_key("dontShowPosterAbstract"):
            self.contribPosterAbstract = False

        self.newPagePerSession = False
        if params.has_key("newPagePerSession"):
            self.newPagePerSession = True

        self.useSessionColorCodes = False
        if params.has_key("useSessionColorCodes"):
            self.useSessionColorCodes = True

        self.showSessionTOC = False
        if params.has_key("showSessionTOC"):
            self.showSessionTOC = True

        self.lengthContribs = False
        if params.has_key("showLengthContribs"):
            self.lengthContribs = True

        self.contribsAtConfLevel = False
        if params.has_key("showContribsAtConfLevel"):
            self.contribsAtConfLevel = True

        self.breaksAtConfLevel = False
        if params.has_key("showBreaksAtConfLevel"):
            self.breaksAtConfLevel = True

        self.dateCloseToSessions = False
        if params.has_key("printDateCloseToSessions"):
            self.dateCloseToSessions = True

        self.coverPage=True
        if not params.has_key("showCoverPage"):
            self.coverPage = False

        self.tableContents=True
        if not params.has_key("showTableContents"):
            self.tableContents = False

        self.logo = False

    def showContribId(self):
        return self.contribId

    def showSpeakerTitle(self):
        return self.speakerTitle

    def showContribAbstract(self):
        return self.contribAbstract

    def showContribPosterAbstract(self):
        return self.contribPosterAbstract

    def showLogo(self):
        return self.logo

    def showNewPagePerSession(self):
        return self.newPagePerSession

    def showUseSessionColorCodes(self):
        return self.useSessionColorCodes

    def showTitleSessionTOC(self):
        return self.showSessionTOC

    def showLengthContribs(self):
        return self.lengthContribs

    def showContribsAtConfLevel(self):
        return self.contribsAtConfLevel

    def showBreaksAtConfLevel(self):
        return self.breaksAtConfLevel

    def showDateCloseToSessions(self):
        return self.dateCloseToSessions

    def showCoverPage(self):
        return self.coverPage

    def showTableContents(self):
        return self.tableContents


def sortEntries(x,y):
    if cmp(x.getStartDate(), y.getStartDate()):
        return cmp(x.getStartDate(), y.getStartDate())
    elif isinstance(x.getOwner(), conference.SessionSlot) and \
            isinstance(y.getOwner(), conference.SessionSlot):
        val = cmp(x.getOwner().getSession().getCode(), y.getOwner().getSession().getCode())

        if val:
            return val
        else:
            return cmp(x.getOwner().getSession().getTitle(), y.getOwner().getSession().getTitle())
    else:
        return cmp(x.getTitle(), y.getTitle())

class TimeTablePlain(PDFWithTOC):

    def __init__(self,conf,aw,showSessions=[],showDays=[],sortingCrit=None, ttPDFFormat=None,
                 pagesize='A4', fontsize = 'normal', firstPageNumber = 1, showSpeakerAffiliation=False, tz=None):
        self._conf=conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._aw=aw
        self._tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        self._showSessions=showSessions
        self._showDays=showDays
        self._ttPDFFormat = ttPDFFormat or TimetablePDFFormat()
        story=[]
        if self._ttPDFFormat.showCoverPage():
            story=None
        PDFWithTOC.__init__(self, story=story, pagesize = pagesize, fontsize=fontsize, firstPageNumber = firstPageNumber)
        self._title= _("Programme")
        self._doc.leftMargin=1*cm
        self._doc.rightMargin=1*cm
        self._doc.topMargin=1.5*cm
        self._doc.bottomMargin=1*cm
        self._sortingCrit=sortingCrit
        self._firstPageNumber = firstPageNumber
        self._showSpeakerAffiliation = showSpeakerAffiliation

    def _processTOCPage(self):
        if self._ttPDFFormat.showTableContents():
            style1 = ParagraphStyle({})
            style1.fontName = "Times-Bold"
            style1.fontSize = modifiedFontSize(18, self._fontsize)
            style1.leading = modifiedFontSize(22, self._fontsize)
            style1.alignment = TA_CENTER
            self._story.append(Spacer(inch, 1*cm))
            p = Paragraph( _("Table of contents"), style1)
            self._story.append(p)
            self._story.append(Spacer(inch, 1*cm))
            if len(self._showSessions)>0:
                style2=ParagraphStyle({})
                style2.fontSize=modifiedFontSize(14, self._fontsize)
                style2.leading=modifiedFontSize(10, self._fontsize)
                style2.alignment=TA_CENTER
                caption=[]
                for sessionId in self._showSessions:
                    session=self._conf.getSessionById(sessionId)
                    if session is not None:
                        caption.append(session.getTitle())
                p=Paragraph("%s"%"\n".join(caption),style2)
                self._story.append(p)
            self._story.append(Spacer(inch, 2*cm))
            self._story.append(self._toc)
            self._story.append(PageBreak())

    def firstPage(self,c,doc):
        if self._ttPDFFormat.showCoverPage():
            c.saveState()
            if self._ttPDFFormat.showLogo():
                self._drawLogo(c, False)
            height = self._drawWrappedString(c, self._conf.getTitle())
            c.setFont('Times-Bold',modifiedFontSize(15, self._fontsize))
            height-=2*cm
            c.drawCentredString(self._PAGE_WIDTH/2.0,height,
                    "%s - %s"%(self._conf.getAdjustedStartDate(self._tz).strftime("%A %d %B %Y"),
                    self._conf.getAdjustedEndDate(self._tz).strftime("%A %d %B %Y")))
            if self._conf.getLocation():
                height-=2*cm
                c.drawCentredString(self._PAGE_WIDTH/2.0,height,escape(self._conf.getLocation().getName()))
            c.setFont('Times-Bold', modifiedFontSize(30, self._fontsize))
            height-=1*cm
            c.drawCentredString(self._PAGE_WIDTH/2.0,height,\
                    self._title)
            self._drawWrappedString(c, "%s / %s"%(self._conf.getTitle(),self._title), width=inch, height=0.75*inch, font='Times-Roman', size=modifiedFontSize(9, self._fontsize), color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
            c.drawRightString(self._PAGE_WIDTH-inch,0.75*inch,
                    nowutc().strftime("%A %d %B %Y"))
            c.restoreState()

    def laterPages(self,c,doc):

        c.saveState()
        maxi=self._PAGE_WIDTH-2*cm
        if doc.getCurrentPart().strip() != "":
            maxi=self._PAGE_WIDTH-6*cm
        self._drawWrappedString(c, "%s / %s"%(self._conf.getTitle(),self._title), width=1*cm, height=self._PAGE_HEIGHT-1*cm, font='Times-Roman', size=modifiedFontSize(9, self._fontsize), color=(0.5,0.5,0.5), align="left", lineSpacing=0.3, maximumWidth=maxi)
        c.drawCentredString(self._PAGE_WIDTH/2.0,0.5*cm,i18nformat(""" _("Page") %d """)%(doc.page + self._firstPageNumber - 1))
        c.drawRightString(self._PAGE_WIDTH-1*cm,self._PAGE_HEIGHT-1*cm,doc.getCurrentPart())
        c.restoreState()

    def _defineStyles(self):
        self._styles={}

        dayStyle=getSampleStyleSheet()["Heading1"]
        dayStyle.fontSize = modifiedFontSize(dayStyle.fontSize, self._fontsize)
        self._styles["day"]=dayStyle

        sessionTitleStyle=getSampleStyleSheet()["Heading2"]
        sessionTitleStyle.fontSize = modifiedFontSize(12.0, self._fontsize)
        self._styles["session_title"]=sessionTitleStyle

        sessionDescriptionStyle=getSampleStyleSheet()["Heading2"]
        sessionDescriptionStyle.fontSize = modifiedFontSize(10.0, self._fontsize)
        self._styles["session_description"] = sessionDescriptionStyle

        self._styles["table_body"]=getSampleStyleSheet()["Normal"]

        convenersStyle=getSampleStyleSheet()["Normal"]
        convenersStyle.fontSize = modifiedFontSize(10.0, self._fontsize)
        convenersStyle.leftIndent=10
        self._styles["conveners"]=convenersStyle

        subContStyle=getSampleStyleSheet()["Normal"]
        subContStyle.fontSize=modifiedFontSize(10.0, self._fontsize)
        subContStyle.leftIndent=15
        self._styles["subContrib"]=subContStyle

    def _HTMLColorToRGB(self, colorstring):
        """ convert #RRGGBB to an (R, G, B) tuple """
        colorstring = colorstring.strip()
        if colorstring[0] == '#': colorstring = colorstring[1:]
        if len(colorstring) != 6:
            raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [float(int(n, 16))/256 for n in (r, g, b)]
        #raise MaKaCError(str((r,g,b)))
        return (r, g, b)

    def _getSessionColor(self,ses):
        HTMLcolor = ses.getSession().getColor()
        color = self._HTMLColorToRGB(HTMLcolor)
        return color

    def _processContribution(self,contrib,l):
        if not contrib.canAccess(self._aw):
            return
        date = "%s"%escape(contrib.getAdjustedStartDate(self._tz).strftime("%H:%M"))
        #date="<font size=\"" + str(modifiedFontSize(10, self._fontsize)) + "\">%s</font>"%date
        #date=self._fontify(date,10)
        #date.style=self._styles["table_body"]
        date=Paragraph(date,self._styles["table_body"])
        lt=[]
        captionText="[%s] %s"%(escape(contrib.getId()),escape(contrib.getTitle()))
        if not self._ttPDFFormat.showContribId():
            captionText="%s"%(escape(contrib.getTitle()))
        if self._ttPDFFormat.showLengthContribs():
            captionText="%s (%s)"%(captionText, escape((datetime(1900,1,1)+contrib.getDuration()).strftime("%Hh%M'")))
        if self._ttPDFFormat.showContribAbstract():
            captionText="<font name=\"Times-Bold\"><b>%s</b></font>"%captionText
        captionText="<font size=\"" + str(modifiedFontSize(10, self._fontsize)) + "\">%s</font>"%captionText
        lt.append([self._fontify(captionText,10)])
        colorCell = ""
        if self._useColors():
            colorCell = " "
        if self._ttPDFFormat.showContribAbstract():
            spkList=[]
            for spk in contrib.getSpeakerList():
                spkName = spk.getFullName()
                if not self._ttPDFFormat.showSpeakerTitle():
                    spkName = self._getNameWithoutTitle(spk)
                if self._showSpeakerAffiliation and spk.getAffiliation().strip() != "":
                    spkName += " (" + spk.getAffiliation() + ")"
                spkList.append(spkName)
            if len(spkList) > 0:
                if len(spkList) == 1:
                    speakerWord = i18nformat(""" _("Presenter"): """)
                else:
                    speakerWord = i18nformat(""" _("Presenters"): """)
                speakerText = speakerWord + ", ".join(spkList)
                speakerText = "<font name=\"Times-Italic\"><i>%s</i></font>"%speakerText
                lt.append([self._fontify(speakerText,9)])
            captionText=escape(contrib.getDescription())
            lt.append([self._fontify(captionText,9)])
            captionAndSpeakers = Table(lt,colWidths=(None),style=self._tsSpk)
            if colorCell != "":
                l.append([colorCell,date,captionAndSpeakers])
            else:
                l.append([date,captionAndSpeakers])
        else:
            caption = Table(lt,colWidths=(None),style=self._tsSpk)
            spkList=[]
            for spk in contrib.getSpeakerList():
                spkName = spk.getFullName()
                if not self._ttPDFFormat.showSpeakerTitle():
                    spkName = self._getNameWithoutTitle(spk)
                if self._showSpeakerAffiliation and spk.getAffiliation().strip() != "":
                    spkName += " (" + spk.getAffiliation() + ")"
                p=Paragraph(escape(spkName),self._styles["table_body"])
                spkList.append([p])
            if len(spkList)==0:
                spkList=[[""]]
            speakers=Table(spkList,style=self._tsSpk)
            if colorCell != "":
                l.append([colorCell,date,caption,speakers])
            else:
                l.append([date,caption,speakers])
        for subc in contrib.getSubContributionList():
            if not subc.canAccess(self._aw):
                return
            lt=[]
            captionText="- [%s] %s"%(escape(subc.getId()),escape(subc.getTitle()))
            if not self._ttPDFFormat.showContribId():
                captionText="- %s"%(escape(subc.getTitle()))
            if self._ttPDFFormat.showLengthContribs():
                captionText="%s (%s)"%(captionText, escape((datetime(1900,1,1)+subc.getDuration()).strftime("%Hh%M'")))
            captionText="<font size=\"" + str(modifiedFontSize(10, self._fontsize)) + "\">%s</font>"%captionText
            lt.append([Paragraph(captionText,self._styles["subContrib"])])
            if self._ttPDFFormat.showContribAbstract():
                captionText="<font size=\"" + str(modifiedFontSize(9, self._fontsize)) + "\">%s</font>"%(escape(subc.getDescription()))
                lt.append([Paragraph(captionText,self._styles["subContrib"])])
            spkList=[]
            for spk in subc.getSpeakerList():
                spkName = spk.getFullName()
                if not self._ttPDFFormat.showSpeakerTitle():
                    spkName = self._getNameWithoutTitle(spk)
                p=Paragraph(escape(spkName),self._styles["table_body"])
                spkList.append([p])
            if len(spkList)==0:
                spkList=[[""]]
            if self._ttPDFFormat.showContribAbstract():
                lt = spkList+lt
                captionAndSpeakers = Table(lt,colWidths=(None),style=self._tsSpk)
                if colorCell != "":
                    l.append([colorCell,"",captionAndSpeakers])
                else:
                    l.append(["",captionAndSpeakers])
            else:
                caption = Table(lt,colWidths=(None),style=self._tsSpk)
                speakers=Table(spkList,style=self._tsSpk)
                if colorCell != "":
                    l.append([colorCell,"",caption,speakers])
                else:
                    l.append(["",caption,speakers])


    def _processPosterContribution(self,contrib,l):
        if not contrib.canAccess(self._aw):
            return
        lt=[]
        captionText="[%s] %s"%(escape(contrib.getId()),escape(contrib.getTitle()))
        if not self._ttPDFFormat.showContribId():
            captionText="%s"%(escape(contrib.getTitle()))
        if self._ttPDFFormat.showLengthContribs():
            captionText="%s (%s)"%(captionText, escape((datetime(1900,1,1)+contrib.getDuration()).strftime("%Hh%M'")))
        captionText="<font name=\"Times-Bold\">%s</font>"%captionText
        lt.append([self._fontify(captionText,10)])
        boardNumber="%s"%escape(contrib.getBoardNumber())
        if self._ttPDFFormat.showContribAbstract() and self._ttPDFFormat.showContribPosterAbstract():
            spkList=[]
            for spk in contrib.getSpeakerList():
                spkName = spk.getFullName()
                if not self._ttPDFFormat.showSpeakerTitle():
                    spkName = self._getNameWithoutTitle(spk)
                if self._showSpeakerAffiliation and spk.getAffiliation().strip() != "":
                    spkName += " (" + spk.getAffiliation() + ")"
                spkList.append(spkName)
            if len(spkList) > 0:
                if len(spkList) == 1:
                    speakerWord = i18nformat(""" _("Presenter"): """)
                else:
                    speakerWord = i18nformat(""" _("Presenters"): """)
                speakerText = speakerWord + ", ".join(spkList)
                speakerText = "<font name=\"Times-Italic\"><i>%s</i></font>"%speakerText
                lt.append([self._fontify(speakerText, 10)])
            captionText=escape(contrib.getDescription())
            lt.append([self._fontify(captionText,9)])
            captionAndSpeakers = Table(lt,colWidths=(None),style=self._tsSpk)
            if self._useColors():
                l.append([" ",captionAndSpeakers,boardNumber])
            else:
                l.append([captionAndSpeakers,boardNumber])
        else:
            caption = Table(lt,colWidths=(None),style=self._tsSpk)
            spkList=[]
            for spk in contrib.getSpeakerList():
                spkName = spk.getFullName()
                if not self._ttPDFFormat.showSpeakerTitle():
                    spkName = self._getNameWithoutTitle(spk)
                p=Paragraph(escape(spkName),self._styles["table_body"])
                spkList.append([p])
            if len(spkList)==0:
                spkList=[[""]]
            speakers=Table(spkList,style=self._tsSpk)
            if self._useColors():
                l.append([" ",caption,speakers, boardNumber])
            else:
                l.append([caption,speakers, boardNumber])
        for subc in contrib.getSubContributionList():
            if not subc.canAccess(self._aw):
                return
            lt=[]
            captionText="- [%s] %s"%(escape(subc.getId()),escape(subc.getTitle()))
            if not self._ttPDFFormat.showContribId():
                captionText="- %s"%(escape(subc.getTitle()))
            if self._ttPDFFormat.showLengthContribs():
                captionText="%s (%s)"%(captionText, escape((datetime(1900,1,1)+subc.getDuration()).strftime("%Hh%M'")))
            lt.append([Paragraph(captionText,self._styles["subContrib"])])
            if self._ttPDFFormat.showContribAbstract():
                captionText="<font size=\"" + str(modifiedFontSize(9, self._fontsize)) + "\">%s</font>"%(escape(subc.getDescription()))
                lt.append([Paragraph(captionText,self._styles["subContrib"])])
            caption = Table(lt,colWidths=(None),style=self._tsSpk)
            spkList=[]
            for spk in subc.getSpeakerList():
                spkName = spk.getFullName()
                if not self._ttPDFFormat.showSpeakerTitle():
                    spkName = self._getNameWithoutTitle(spk)
                p=Paragraph(escape(spkName),self._styles["table_body"])
                spkList.append([p])
            if len(spkList)==0:
                spkList=[[""]]
            speakers=Table(spkList,style=self._tsSpk)
            l.append(["",caption,speakers])

    def _getNameWithoutTitle(self, av):
        res = av.getFamilyName().upper()
        if av.getFirstName() != "":
            res = "%s, %s"%( res, av.getFirstName() )
        return res

    def _useColors(self):
        return self._ttPDFFormat.showUseSessionColorCodes()

    def _fontify(self, text, fSize=10, fName=""):
        style = getSampleStyleSheet()["Normal"]
        style.fontSize=modifiedFontSize(fSize, self._fontsize)
        style.leading=modifiedFontSize(fSize+3, self._fontsize)
        return Paragraph(text,style)

    def _fontifyRow(self, row, fSize=10, fName=""):
        newrow = []
        for text in row:
            newrow.append(self._fontify(text,fSize,fName))
        return newrow

    def _processDayEntries(self,day,story):
        res=[]
        originalts=TableStyle([('VALIGN',(0,0),(-1,-1),"TOP"),
                        ('LEFTPADDING',(0,0),(-1,-1),1),
                        ('RIGHTPADDING',(0,0),(-1,-1),1),
                        ('GRID',(0,1),(-1,-1),1,colors.lightgrey)])
        self._tsSpk=TableStyle([("LEFTPADDING",(0,0),(0,-1),0),
                            ("RIGHTPADDING",(0,0),(0,-1),0),
                            ("TOPPADDING",(0,0),(0,-1),1),
                            ("BOTTOMPADDING",(0,0),(0,-1),0)])
        colorts=TableStyle([("LEFTPADDING",(0,0),(-1,-1),3),
                            ("RIGHTPADDING",(0,0),(-1,-1),0),
                            ("TOPPADDING",(0,0),(-1,-1),0),
                            ("BOTTOMPADDING",(0,0),(-1,-1),0),
                            ('GRID',(0,0),(0,-1),1,colors.lightgrey)])
        entriesOnDay=self._conf.getSchedule().getEntriesOnDay(day)
        entriesOnDay.sort(sortEntries)
        for entry in entriesOnDay:
            #Session slot
            if isinstance(entry,schedule.LinkedTimeSchEntry) and \
                    isinstance(entry.getOwner(),conference.SessionSlot):
                sessionSlot=entry.getOwner()
                if len(self._showSessions)>0 and \
                    sessionSlot.getSession().getId() not in self._showSessions:
                    continue
                if not sessionSlot.canView(self._aw):
                    continue
                room=""
                if sessionSlot.getRoom() is not None:
                    room=" - %s"%escape(sessionSlot.getRoom().getName())
                sesCaption="%s"%sessionSlot.getSession().getTitle()
                if sessionSlot.getTitle()!="":
                    sesCaption="%s: %s"%(sesCaption,sessionSlot.getTitle())
                conv=[]
                for c in sessionSlot.getOwnConvenerList():
                    if self._showSpeakerAffiliation and c.getAffiliation().strip() != "":
                        conv.append("%s (%s)"%(escape(c.getFullName()), escape(c.getAffiliation())))
                    else:
                        conv.append(escape(c.getFullName()))
                conv="; ".join(conv)
                if conv!="":
                    conv=i18nformat("""<font name=\"Times-Bold\"><b>- _("Conveners"): %s</b></font>""")%conv
                res.append(Paragraph("",self._styles["session_title"]))
                startDateStr = escape(sessionSlot.getAdjustedStartDate(self._tz).strftime("%H:%M"))
                if self._ttPDFFormat.showDateCloseToSessions():
                    startDateStr = escape(sessionSlot.getAdjustedStartDate(self._tz).strftime("%d %B %H:%M"))
                text="""<u>%s</u>%s (%s-%s)"""%(
                        escape(sesCaption),room,
                        #escape(sessionSlot.getStartDate().strftime("%d %B %H:%M")),
                        #escape(sessionSlot.getEndDate().strftime("%H:%M")))
                        startDateStr,
                        escape(sessionSlot.getAdjustedEndDate(self._tz).strftime("%H:%M")))
                p1=Paragraph(text,self._styles["session_title"])
                if self._useColors():
                    l = [["",p1]]
                    widths=[0.2*cm,None]
                    ts = deepcopy(colorts)
                    ts.add('BACKGROUND', (0, 0), (0,-1), self._getSessionColor(sessionSlot))
                    p1 = Table(l,colWidths=widths,style=ts)
                res.append(p1)
                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1]={"text":escape(sessionSlot.getSession().getTitle()), "level":2}
##                if self._useColors():
##                    l = [["",p1]]
##                    widths=[0.2*cm,None]
##                    ts = deepcopy(colorts)
##                    ts.add('BACKGROUND', (0, 0), (0,-1), self._getSessionColor(sessionSlot))
##                    res.append(Table(l,colWidths=widths,style=ts))
##                else:
##                    res.append(p1)
                #add session description
                if sessionSlot.getSession().getDescription():
                    text = "<i>%s</i>"%escape(sessionSlot.getSession().getDescription())
                    p = Paragraph(text,self._styles["session_description"])
                    res.append(p)
                p2=Paragraph(conv,self._styles["conveners"])
                res.append(p2)
                l=[]
                ts = deepcopy(originalts)
                if sessionSlot.getSession().getScheduleType()=="poster":
                    if self._sortingCrit is not None:
                        cl=[]
                        for sEntry in sessionSlot.getSchedule().getEntries():
                            if isinstance(sEntry,schedule.LinkedTimeSchEntry) and isinstance(sEntry.getOwner(),conference.Contribution):
                                cl.append(sEntry.getOwner())
                        f=filters.SimpleFilter(None,self._sortingCrit)
                        for contrib in f.apply(cl):
                            self._processPosterContribution(contrib,l)
                    else:
                        for sEntry in sessionSlot.getSchedule().getEntries():
                            if isinstance(sEntry,schedule.LinkedTimeSchEntry) and isinstance(sEntry.getOwner(),conference.Contribution):
                                contrib=sEntry.getOwner()
                                self._processPosterContribution(contrib,l)
                    if len(l)>0:
                        title = "[id] title"
                        if not self._ttPDFFormat.showContribId():
                            title = "title"
                        if self._ttPDFFormat.showContribAbstract() and self._ttPDFFormat.showContribPosterAbstract():
                            #presenter integrated in 1st column -> 2 columns only
                            row = [title,"board"]
                            widths=[None,1*cm]
                        else:
                            row = [title,"presenter","board"]
                            widths=[None,5*cm,1*cm]
                        row = self._fontifyRow(row,11)
                        if self._useColors():
                            row.insert(0,"")
                            widths.insert(0,0.2*cm)
                        l.insert(0,row)
                        if self._useColors():
                            ts.add('BACKGROUND', (0, 1), (0,-1), self._getSessionColor(sessionSlot))
                        t=Table(l,colWidths=widths,style=ts)
                else: #it's not a poster
                    for sEntry in sessionSlot.getSchedule().getEntries():
                        if isinstance(sEntry,schedule.LinkedTimeSchEntry) and isinstance(sEntry.getOwner(),conference.Contribution):
                            contrib=sEntry.getOwner()
                            self._processContribution(contrib,l)
                        elif isinstance(sEntry,schedule.BreakTimeSchEntry):
##                            date="%s"%escape(sEntry.getStartDate().strftime("%H:%M"))
##                            date=self._fontify(date,10)
                            date="%s"%escape(sEntry.getAdjustedStartDate(self._tz).strftime("%H:%M"))
                            date=self._fontify(date,10)

                            lt=[]
                            captionText="%s"%escape(sEntry.getTitle())
                            if self._ttPDFFormat.showLengthContribs():
                                captionText="%s (%s)"%(captionText, escape((datetime(1900,1,1)+sEntry.getDuration()).strftime("%Hh%M'")))
                            lt.append([self._fontify(captionText,10)])
                            caption = Table(lt,colWidths=(None),style=self._tsSpk)
                            if self._ttPDFFormat.showContribAbstract():
                                row = [date,caption]
                            else:
                                row = [date,caption,""]
                            if self._useColors():
                                row.insert(0,"")
                            l.append(row)
                    if len(l)>0:
                        title = "[id] title"
                        if not self._ttPDFFormat.showContribId():
                            title = "title"
                        if self._ttPDFFormat.showContribAbstract():
                            #presenter integrated in 1st column -> 2 columns only
                            row = ["time",title]
                            widths = [1*cm,None]
                        else:
                            row = ["time",title,"presenter"]
                            widths = [1*cm,None,5*cm]
                        row = self._fontifyRow(row,11)
                        if self._useColors():
                            row.insert(0,"")
                            widths.insert(0,0.2*cm)
                        l.insert(0,row)
                        if self._useColors():
                            ts.add('BACKGROUND', (0, 1), (0,-1), self._getSessionColor(sessionSlot))
                        t=Table(l,colWidths=widths,style=ts)
                if len(l)>0:
                    res.append(t)
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())
                elif entry == entriesOnDay[-1]: # if it is the last one, we do the page break and remove the previous one.
                    i=len(res)-1
                    while i>=0:
                        if isinstance(res[i], PageBreak):
                            del res[i]
                            break
                        i-=1
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())
            #contribution
            elif self._ttPDFFormat.showContribsAtConfLevel() and \
                 isinstance(entry,schedule.LinkedTimeSchEntry) and \
                 isinstance(entry.getOwner(),conference.Contribution):
                contrib=entry.getOwner()
                if not contrib.canView(self._aw):
                        continue
                room=""
                if contrib.getRoom() is not None:
                    room=" - %s"%escape(contrib.getRoom().getName())
                caption="%s"%contrib.getTitle()
                spks=[]
                for c in contrib.getSpeakerList():
                    if self._showSpeakerAffiliation and c.getAffiliation().strip() != "":
                        spks.append("%s (%s)"%(escape(c.getFullName()), escape(c.getAffiliation())))
                    else:
                        spks.append(escape(c.getFullName()))
                spks="; ".join(spks)
                if spks.strip()!="":
                    spks=i18nformat("""<font name=\"Times-Bold\"><b>- _("Presenters"): %s</b></font>""")%spks
                text="""<u>%s</u>%s (%s-%s)"""%(
                        escape(caption),room,
                        escape(contrib.getAdjustedStartDate(self._tz).strftime("%H:%M")),
                        escape(contrib.getAdjustedEndDate(self._tz).strftime("%H:%M")))
                p1=Paragraph(text,self._styles["session_title"])
                res.append(p1)
                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1]={"text":escape(contrib.getTitle()), "level":2}
                p2=Paragraph(spks,self._styles["conveners"])
                res.append(p2)
                if entry == entriesOnDay[-1]: # if it is the last one, we do the page break and remove the previous one.
                    i=len(res)-1
                    while i>=0:
                        if isinstance(res[i], PageBreak):
                            del res[i]
                            break
                        i-=1
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())
            #break
            elif self._ttPDFFormat.showBreaksAtConfLevel() and \
                 isinstance(entry,schedule.BreakTimeSchEntry):
                breakE=entry
                room=""
                if breakE.getRoom() is not None:
                    room=" - %s"%escape(breakE.getRoom().getName())
                caption="%s"%breakE.getTitle()
                text="""<u>%s</u>%s (%s-%s)"""%(
                        escape(caption),room,
                        escape(breakE.getAdjustedStartDate(self._tz).strftime("%H:%M")),
                        escape(breakE.getAdjustedEndDate(self._tz).strftime("%H:%M")))
                p1=Paragraph(text,self._styles["session_title"])
                res.append(p1)
                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1]={"text":escape(breakE.getTitle()), "level":2}
                if entry == entriesOnDay[-1]: # if it is the last one, we do the page break and remove the previous one.
                    i=len(res)-1
                    while i>=0:
                        if isinstance(res[i], PageBreak):
                            del res[i]
                            break
                        i-=1
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())

        return res


    def getBody(self,story=None):
        self._defineStyles()
        if not story:
            story=self._story
        if not self._ttPDFFormat.showCoverPage():
            s = ParagraphStyle({})
            s.fontName = "Times-Bold"
            s.fontSize = 18
            s.leading = 22
            s.alignment = TA_CENTER
            p=Paragraph(escape(self._conf.getTitle()),s)
            story.append(p)
            story.append(Spacer(1,0.4*inch))

        currentDay=self._conf.getSchedule().getAdjustedStartDate(self._tz)
        while currentDay.strftime("%Y-%m-%d")<=self._conf.getSchedule().getAdjustedEndDate(self._tz).strftime("%Y-%m-%d"):
            if len(self._showDays)>0 and \
                    currentDay.strftime("%d-%B-%Y") not in self._showDays:
                currentDay+=timedelta(days=1)
                continue
            dayEntries=self._processDayEntries(currentDay,story)
            if len(dayEntries)==0:
                currentDay+=timedelta(days=1)
                continue
            text=escape(currentDay.strftime("%A %d %B %Y"))
            p=Paragraph(text,self._styles["day"],part=currentDay.strftime("%A %d %B %Y"))
            story.append(p)
            self._indexedFlowable[p]={"text":currentDay.strftime("%A %d %B %Y"), "level":1}
            for entry in dayEntries:
                story.append(entry)
            if not self._ttPDFFormat.showNewPagePerSession():
                story.append(PageBreak())
            currentDay+=timedelta(days=1)

class SimplifiedTimeTablePlain(PDFBase):

    def __init__(self,conf,aw,showSessions=[],showDays=[],sortingCrit=None, ttPDFFormat=None, pagesize = 'A4', fontsize = 'normal', tz=None):
        self._conf=conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._aw=aw
        self._showSessions=showSessions
        self._showDays=showDays
        PDFBase.__init__(self, story=[], pagesize = pagesize)
        self._title= _("Simplified Programme")
        self._doc.leftMargin=1*cm
        self._doc.rightMargin=1*cm
        self._doc.topMargin=1*cm
        self._doc.bottomMargin=1*cm
        self._sortingCrit=sortingCrit
        self._ttPDFFormat = ttPDFFormat or TimetablePDFFormat()
        self._fontsize = fontsize

    def _defineStyles(self):
        self._styles={}
        normalStl=getSampleStyleSheet()["Normal"]
        normalStl.fontName="Courier"
        normalStl.fontSize = modifiedFontSize(10, self._fontsize)
        normalStl.spaceBefore=0
        normalStl.spaceAfter=0
        normalStl.alignment=TA_LEFT
        self._styles["normal"]=normalStl
        titleStl=getSampleStyleSheet()["Normal"]
        titleStl.fontName="Courier-Bold"
        titleStl.fontSize = modifiedFontSize(12, self._fontsize)
        titleStl.spaceBefore=0
        titleStl.spaceAfter=0
        titleStl.alignment=TA_LEFT
        self._styles["title"]=titleStl
        dayStl=getSampleStyleSheet()["Normal"]
        dayStl.fontName="Courier-Bold"
        dayStl.fontSize = modifiedFontSize(10, self._fontsize)
        dayStl.spaceBefore=0
        dayStl.spaceAfter=0
        dayStl.alignment=TA_LEFT
        self._styles["day"]=dayStl

    def _haveSessionSlotsTitles(self, session):
        """Checks if the session has slots with titles or not"""
        for ss in session.getSlotList():
            if ss.getTitle().strip() != "":
                return True
        return False

    def _processDayEntries(self,day,story):
        lastSessions=[] # this is to avoid checking if the slots have titles for all the slots
        res=[]
        for entry in self._conf.getSchedule().getEntriesOnDay(day):
            if isinstance(entry,schedule.LinkedTimeSchEntry) and \
                    isinstance(entry.getOwner(),conference.SessionSlot):
                sessionSlot=entry.getOwner()
                session = sessionSlot.getSession()
                if len(self._showSessions)>0 and \
                    session.getId() not in self._showSessions:
                    continue
                if not sessionSlot.canView(self._aw):
                    continue
                if session in lastSessions:
                    continue
                if self._haveSessionSlotsTitles(session):
                    e=sessionSlot
                else:
                    lastSessions.append(session)
                    e=session
                title=e.getTitle()
                if title.strip()=="":
                    title=e.getOwner().getTitle()
                res.append(Paragraph( i18nformat("""<font name=\"Times-Bold\"><b> _("Session"):</b></font> %s""")%escape(title),self._styles["normal"]))
                roomTime=""
                if sessionSlot.getRoom() is not None:
                    roomTime="%s "%(escape(sessionSlot.getRoom().getName()))
                roomTime= i18nformat("""<font name=\"Times-Bold\"><b> _("Time and Place"):</b></font> %s(%s-%s)""")%(roomTime, sessionSlot.getAdjustedStartDate(self._tz).strftime("%H:%M"), \
                        sessionSlot.getAdjustedEndDate(self._tz).strftime("%H:%M"))
                res.append(Paragraph(roomTime,self._styles["normal"]))
                chairs=[]
                for c in sessionSlot.getOwnConvenerList():
                    chairs.append("%s"%c.getFullName())
                if chairs != []:
                    res.append(Paragraph( i18nformat("""<font name=\"Times-Bold\"><b> _("Chair/s"):</b></font> %s""")%("; ".join(chairs)),self._styles["normal"]))
                res.append(Spacer(1,0.2*inch))
            elif self._ttPDFFormat.showContribsAtConfLevel() and isinstance(entry,schedule.LinkedTimeSchEntry) and \
                    isinstance(entry.getOwner(),conference.Contribution):
                contrib=entry.getOwner()
                if not contrib.canView(self._aw):
                    continue
                title=contrib.getTitle()
                res.append(Paragraph( i18nformat("""<font name=\"Times-Bold\"><b> _("Contribution"):</b></font> %s""")%escape(title),self._styles["normal"]))
                roomTime=""
                if contrib.getRoom() is not None:
                    roomTime="%s "%(escape(contrib.getRoom().getName()))
                roomTime= i18nformat("""<font name=\"Times-Bold\"><b> _("Time and Place"):</b></font> %s(%s-%s)""")%(roomTime, contrib.getAdjustedStartDate(self._tz).strftime("%H:%M"), \
                        contrib.getAdjustedEndDate(self._tz).strftime("%H:%M"))
                res.append(Paragraph(roomTime,self._styles["normal"]))
                spks=[]
                for c in contrib.getSpeakerList():
                    spks.append("%s"%c.getFullName())
                if spks != []:
                    res.append(Paragraph( i18nformat("""<font name=\"Times-Bold\"><b> _("Presenter/s"):</b></font> %s""")%("; ".join(spks)),self._styles["normal"]))
                res.append(Spacer(1,0.2*inch))
            elif self._ttPDFFormat.showBreaksAtConfLevel() and isinstance(entry,schedule.BreakTimeSchEntry):
                title=entry.getTitle()
                res.append(Paragraph( i18nformat("""<font name=\"Times-Bold\"><b> _("Break"):</b></font> %s""")%escape(title),self._styles["normal"]))
                roomTime=""
                if entry.getRoom() is not None:
                    roomTime="%s "%(escape(entry.getRoom().getName()))
                roomTime= i18nformat("""<font name=\"Times-Bold\"><b> _("Time and Place"):</b></font> %s(%s-%s)""")%(roomTime, entry.getAdjustedStartDate(self._tz).strftime("%H:%M"), \
                        entry.getAdjustedEndDate(self._tz).strftime("%H:%M"))
                res.append(Paragraph(roomTime,self._styles["normal"]))
                res.append(Spacer(1,0.2*inch))
        res.append(PageBreak())
        return res

    def getBody(self,story=None):
        self._defineStyles()
        if not story:
            story=self._story
        currentDay=self._conf.getSchedule().getAdjustedStartDate(self._tz)
        while currentDay.strftime("%Y-%m-%d")<=self._conf.getSchedule().getAdjustedEndDate(self._tz).strftime("%Y-%m-%d"):
            if len(self._showDays)>0 and \
                    currentDay.strftime("%d-%B-%Y") not in self._showDays:
                currentDay+=timedelta(days=1)
                continue
            dayEntries=self._processDayEntries(currentDay,story)
            if len(dayEntries)==0:
                currentDay+=timedelta(days=1)
                continue
            if self._conf.getAdjustedEndDate(self._tz).month != self._conf.getAdjustedEndDate(self._tz).month:
                text="%s - %s-%s"%(escape(self._conf.getTitle()), escape(self._conf.getAdjustedStartDate(self._tz).strftime("%d %B %Y")), \
                    escape(self._conf.getAdjustedEndDate(self._tz).strftime("%d %B %Y")) )
            else:
                text="%s - %s-%s"%(escape(self._conf.getTitle()), escape(self._conf.getAdjustedStartDate(self._tz).strftime("%d")), \
                        escape(self._conf.getAdjustedEndDate(self._tz).strftime("%d %B %Y")) )
            if self._conf.getLocation() is not None:
                text="%s, %s."%(text, self._conf.getLocation().getName())
            text="%s"%text
            p=Paragraph(text, self._styles["title"])
            story.append(p)
            text2= i18nformat(""" _("Daily Programme"): %s""")%escape(currentDay.strftime("%A %d %B %Y"))
            p2=Paragraph(text2,self._styles["day"])
            story.append(p2)
            story.append(Spacer(1,0.4*inch))
            for entry in dayEntries:
                story.append(entry)
            currentDay+=timedelta(days=1)

class AbstractBook(PDFWithTOC):

    def __init__(self,conf,aw,tz=None):
        self._conf=conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._aw=aw
        self._sortBy=self._conf.getBOAConfig().getSortBy()
        if self._sortBy.strip()=="" or\
                self._sortBy not in ["number", "name", "sessionTitle", "speaker", "schedule"]:
            self._sortBy="number"
        self._title= _("Book of abstracts")
        PDFWithTOC.__init__(self)

    def firstPage(self,c,doc):
        c.saveState()
        self._drawLogo(c, False)
        height=self._drawWrappedString(c,self._conf.getTitle())
        c.setFont('Times-Bold',15)
        height-=2*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0,height,
                "%s - %s"%(self._conf.getAdjustedStartDate(self._tz).strftime("%A %d %B %Y"),
                self._conf.getAdjustedEndDate(self._tz).strftime("%A %d %B %Y")))
        if self._conf.getLocation():
            height-=1*cm
            c.drawCentredString(self._PAGE_WIDTH/2.0,height,
                    escape(self._conf.getLocation().getName()))
        c.setFont('Times-Bold', 30)
        height-=6*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0,height,\
                self._title)
        self._drawWrappedString(c, "%s / %s"%(self._conf.getTitle(),self._title), width=inch, height=0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
        c.drawRightString(self._PAGE_WIDTH-inch,0.75*inch,
                nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def laterPages(self,c,doc):
        c.saveState()
        c.setFont('Times-Roman',9)
        c.setFillColorRGB(0.5,0.5,0.5)
        c.drawString(1*cm,self._PAGE_HEIGHT-1*cm,
            "%s / %s"%(escape(self._conf.getTitle()),self._title))
        c.drawCentredString(self._PAGE_WIDTH/2.0,0.5*cm,"%d "%doc.page)
        c.restoreState()

    def _defineStyles(self):
        self._styles={}
        titleStyle=getSampleStyleSheet()["Heading1"]
        titleStyle.fontName="LinuxLibertine-Bold"
        titleStyle.fontSize=14.0
        titleStyle.spaceBefore=0
        titleStyle.spaceAfter=10
        titleStyle.leading=14
        self._styles["title"]=titleStyle
        subtitleStyle=getSampleStyleSheet()["Heading1"]
        subtitleStyle.fontName="LinuxLibertine-Bold"
        subtitleStyle.fontSize=11.0
        subtitleStyle.spaceBefore=0
        subtitleStyle.spaceAfter=4
        subtitleStyle.leading=14
        self._styles["subtitle"]=subtitleStyle
        authStyle=getSampleStyleSheet()["Heading3"]
        authStyle.fontName="LinuxLibertine"
        authStyle.fontSize=8.0
        authStyle.spaceBefore=0
        authStyle.spaceAfter=0
        authStyle.leading=14
        self._styles["authors"]=authStyle
        abstractStyle=getSampleStyleSheet()["Normal"]
        abstractStyle.fontName="LinuxLibertine"
        abstractStyle.fontSize=10.0
        abstractStyle.spaceBefore=0
        abstractStyle.spaceAfter=0
        abstractStyle.alignment=TA_JUSTIFY
        self._styles["abstract"]=abstractStyle
        ttInfoStyle=getSampleStyleSheet()["Normal"]
        ttInfoStyle.fontName="LinuxLibertine"
        ttInfoStyle.fontSize=10.0
        ttInfoStyle.spaceBefore=0
        ttInfoStyle.spaceAfter=0
        ttInfoStyle.alignment=TA_JUSTIFY
        self._styles["tt_info"]=ttInfoStyle
        normalStyle=getSampleStyleSheet()["Normal"]
        normalStyle.fontName="LinuxLibertine"
        normalStyle.fontSize=10.0
        normalStyle.spaceBefore=5
        normalStyle.spaceAfter=5
        normalStyle.alignment=TA_JUSTIFY
        self._styles["normal"]=normalStyle

    def _addAuthors(self, authorList, institutions):
        lauth = []
        for auth in authorList:
            fullName=auth.getFullName()
            instit=auth.getAffiliation().strip()
            if instit!="":
                try:
                    indexInsti = institutions.index(instit) + 1
                except:
                    institutions.append(instit)
                    indexInsti = len(institutions)
                fullName="%s <sup>%s</sup>"%(fullName,indexInsti)
            lauth.append("%s"%escape(fullName))
        return lauth

    def _addContribution(self, contrib, story):
        if not contrib.canAccess(self._aw):
            return
        paragraphs=[]
        ses=""
        if contrib.getSession() is not None:
            ses=contrib.getSession().getTitle()
        if contrib.getBoardNumber():
            if ses != "":
                ses = "%s - "%ses
                ses="%sBoard %s"%(ses, contrib.getBoardNumber())
        if ses!="":
            ses = "%s / "%ses

        caption = "%s%s"%(ses,contrib.getId())
        paragraphs.append(Paragraph(escape(caption),self._styles["subtitle"]))
        caption="%s"%(contrib.getTitle())
        p = Paragraph(escape(caption),self._styles["title"])
        paragraphs.append(p)
        flowableText = escape(contrib.getTitle())
        if self._conf.getBOAConfig().getShowIds():
            flowableText += """ (%s)"""%contrib.getId()
        self._indexedFlowable[p] = {"text":escape(flowableText), "level":1}

        lauth=[]
        institutions=[]
        authors = self._addAuthors(contrib.getPrimaryAuthorList(), institutions)
        if authors and contrib.getCoAuthorList():
            authors = i18nformat("""<b>_("%s"):</b> %s""")%(ngettext("Author", "Authors", len(authors)), "; ".join(authors))
        else:
            authors = "; ".join(authors)
        paragraphs.append(Paragraph(authors, self._styles["authors"]))
        coauthors = self._addAuthors(contrib.getCoAuthorList(), institutions)
        if coauthors:
            paragraphs.append(Paragraph(i18nformat("""<b>_("Co-%s"):</b> %s""")%(ngettext("Author", "Authors", len(coauthors)), "; ".join(coauthors)),self._styles["authors"]))
        if institutions:
            linst=[]
            for instit in institutions:
                linst.append("<sup>%s</sup> <i>%s</i>"%(institutions.index(instit)+1, instit))
            institutionsText="<br/>".join(linst)
            paragraphs.append(Paragraph(institutionsText,self._styles["authors"]))

        if self._conf.getBOAConfig().getCorrespondingAuthor() == "submitter":
            submitterEmail=""
            if isinstance(contrib, conference.AcceptedContribution):
                submitterEmail=contrib.getAbstract().getSubmitter().getEmail()
            elif contrib.getSubmitterList():
                submitterEmail=contrib.getSubmitterList()[0].getEmail()

            if submitterEmail!="":
                submitter = i18nformat("""<b>_("Corresponding Author"):</b> %s""")%submitterEmail
                paragraphs.append(Paragraph(escape(submitter),self._styles["normal"]))
        elif self._conf.getBOAConfig().getCorrespondingAuthor() == "speakers":
            speakersEmail = [speaker.getEmail() for speaker in contrib.getSpeakerList()]
            if speakersEmail:
                speakers = i18nformat("""<b>_("Corresponding %s"):</b> %s""")%(ngettext("Author", "Authors", len(speakersEmail)), ", ".join(speakersEmail))
                paragraphs.append(Paragraph(escape(speakers),self._styles["normal"]))
        abstract = contrib.getDescription()
        paragraphs.append(Paragraph(escape(abstract), self._styles["abstract"]))

        abs=KeepTogether(paragraphs)
        story.append(abs)
        story.append(Spacer(1,0.4*inch))

    def getBody(self,story=None):
        self._defineStyles()
        if not story:
            story=self._story
        if self._conf.getBOAConfig().getText():
            text=self._conf.getBOAConfig().getText().replace("<BR>","<br>")
            text=text.replace("<Br>","<br>")
            text=text.replace("<bR>","<br>")
            for par in text.split("<br>"):
                p=Paragraph(par,self._styles["normal"])
                story.append(p)
            story.append(PageBreak())
        if self._sortBy == "schedule":
            for entry in self._conf.getSchedule().getEntries():
                if isinstance(entry,schedule.LinkedTimeSchEntry) and isinstance(entry.getOwner(),conference.SessionSlot):
                    if entry.getOwner().canAccess(self._aw):
                        for slotentry in entry.getOwner().getSchedule().getEntries():
                            if isinstance(slotentry.getOwner(), conference.Contribution):
                                self._addContribution(slotentry.getOwner(), story)
                elif isinstance(entry,schedule.LinkedTimeSchEntry) and isinstance(entry.getOwner(),conference.Contribution):
                    self._addContribution(entry.getOwner(), story)
        else:
            fc=FilterCriteria(self._conf,{"status":[ContribStatusList.getId(conference.ContribStatusSch),ContribStatusList.getId(conference.ContribStatusNotSch)]})
            sc=contribFilters.SortingCriteria((self._sortBy,))
            f=filters.SimpleFilter(fc,sc)
            for contrib in f.apply(self._conf.getContributionList()):
                self._addContribution(contrib, story)


class FilterCriteria(filters.FilterCriteria):
    _availableFields = {
        contribFilters.StatusFilterField.getId():contribFilters.StatusFilterField
                }

class ProceedingsTOC(PDFBase):

    def __init__(self, conf, trackDict=None, trackOrder=None, contribList=None, npages=None, doc=None, story=None, tz=None):
        self._conf = conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        self._trackDict = trackDict
        self._trackOrder = trackOrder
        self._contribDictNPages = npages
        self._contribList=contribList
        if not story:
            story = [Spacer(inch, 5*cm)]
        PDFBase.__init__(self, doc, story)
        self._title = _("Proceedings")
        self._PAGE_HEIGHT = defaultPageSize[1]
        self._PAGE_WIDTH = defaultPageSize[0]

    def firstPage(self,c,doc):
        c.saveState()
        self._drawLogo(c, False)
        height=self._drawWrappedString(c, self._conf.getTitle())
        c.setFont('Times-Bold',15)
        height-=2*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0,height,
                "%s - %s"%(self._conf.getAdjustedStartDate(self._tz).strftime("%A %d %B %Y"),
                self._conf.getAdjustedEndDate(self._tz).strftime("%A %d %B %Y")))
        if self._conf.getLocation():
            height-=1*cm
            c.drawCentredString(self._PAGE_WIDTH/2.0,height,escape(self._conf.getLocation().getName()))
        c.setFont('Times-Bold', 30)
        height-=6*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0,height,self._title)
        c.setFont('Times-Roman',9)
        c.setFillColorRGB(0.5,0.5,0.5)
        c.restoreState()

    def laterPages(self,c,doc):
        c.saveState()
        location = ""
        if self._conf.getLocation() is not None and self._conf.getLocation().getName().strip() != "":
            location = " - %s"%(escape(self._conf.getLocation().getName()))
        self._drawWrappedString(c, "%s%s"%(escape(self._conf.getTitle()), location), width=0.5*inch, height=self._PAGE_HEIGHT-0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-inch, measurement=inch, lineSpacing=0.15)
        c.drawCentredString(self._PAGE_WIDTH/2.0,0.5*cm,"%s "%Int2Romans.int_to_roman(doc.page-1))
        c.restoreState()

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story
        self._story.append(PageBreak())
        style = ParagraphStyle({})
        style.fontName = "Times-Bold"
        style.fontSize = 20
        style.spaceBefore=0
        style.spaceAfter=8
        style.leading=14
        style.alignment=TA_LEFT
        text = _("Table of Contents")
        p = Paragraph(text, style)
        story.append(p)

        story.append(Spacer(inch, 0.5*cm))

        styleAuthor = ParagraphStyle({})
        styleAuthor.leading = 10
        styleAuthor.fontName = "Times-Roman"
        styleAuthor.fontSize = 8
        styleAuthor.spaceBefore=0
        styleAuthor.spaceAfter=0
        styleAuthor.alignment=TA_LEFT
        styleAuthor.leftIndent=10
        styleAuthor.firstLineIndent=0

        styleContrib = ParagraphStyle({})
        styleContrib.leading = 12
        styleContrib.fontName = "Times-Roman"
        styleContrib.fontSize = 10
        styleContrib.spaceBefore=0
        styleContrib.spaceAfter=0
        styleContrib.alignment=TA_LEFT
        styleContrib.leftIndent=0
        styleContrib.firstLineIndent=0
        styleContrib.leftIndent=0

        styleTrack = ParagraphStyle({})
        styleTrack.fontName = "Times-Bold"
        styleTrack.fontSize = 12
        styleTrack.spaceBefore=40
        styleTrack.spaceAfter=30
        styleTrack.alignment=TA_LEFT

        tsContribs=TableStyle([('VALIGN',(0,0),(-1,0),"BOTTOM"),
                        ('VALIGN',(0,0),(-1,-1),"BOTTOM"),
                        ('ALIGN',(0,1),(-1,1),"RIGHT"),
                        ('BOTTOMPADDING',(0,0),(-1,-1),0),
                        ('TOPPADDING',(0,0),(-1,-1),0)])
        i = 1
        if self._trackOrder is not None and self._trackOrder!=[]:
            for track in self._trackOrder:
                l=[]
                p=Paragraph("",styleTrack)
                p2=Paragraph("",styleTrack)
                l.append([p, p2])
                p=Paragraph(escape(track.getTitle()),styleTrack)
                p2=Paragraph("<b>%s</b>"%escape("%s"%i),styleTrack)
                i += 2
                l.append([p, p2])
                p=Paragraph("",styleTrack)
                p2=Paragraph("",styleTrack)
                l.append([p, p2])
                l.append(["", ""])
                for contrib in self._trackDict[track.getId()]:
                    i=self._addContrib(contrib, l, i, styleContrib, styleAuthor )
                l.append(["", ""])
                t=Table(l,colWidths=(None,1.2*cm),style=tsContribs)
                self._story.append(t)
        else:
            l=[]
            for contrib in self._contribList:
                i=self._addContrib(contrib, l, i, styleContrib, styleAuthor)
            if l!=[]:
                t=Table(l,colWidths=(None,1.2*cm),style=tsContribs)
                self._story.append(t)
        self._story.append(Spacer(inch, 2*cm))

        return story

    def _addContrib(self, contrib, l, i, styleContrib, styleAuthor):
        authorList = []
        for author in contrib.getPrimaryAuthorList():
            authorList.append(self._getAbrName(author))
        for author in contrib.getCoAuthorList():
            authorList.append(self._getAbrName(author))
        if authorList == []:
            for author in contrib.getSpeakerList():
                authorList.append(self._getAbrName(author))
        p=Paragraph(escape(contrib.getTitle()), styleContrib)
        p2=Paragraph("""<i>%s</i>"""%(escape(", ".join(authorList))), styleAuthor)
        p3=Paragraph("""<font size="10">%s</font>"""%escape("%s"%i),styleAuthor)
        i += self._contribDictNPages[contrib.getId()]
        l.append([p, ""])
        l.append([p2, p3])
        l.append(["", ""])
        return i

    def _getAbrName(self, author):
        res = author.getFamilyName()
        if res.strip() != "" and len(res)>1:
            res = "%s%s"%(res[0].upper(), res[1:].lower())
        if author.getFirstName() != "":
            if res == "":
                res = author.getFirstName()
            else:
                res = "%s. %s"%(author.getFirstName()[0].upper(), res)
        return res

class ProceedingsChapterSeparator(PDFBase):

    def __init__(self, track, doc=None, story=None):
        self._track = track
        self._conf = track.getConference()
        if not story:
            story = [Spacer(inch, 5*cm)]
        PDFBase.__init__(self, doc, story)
        self._title = _("Proceedings")
        self._PAGE_HEIGHT = defaultPageSize[1]
        self._PAGE_WIDTH = defaultPageSize[0]

    def firstPage(self,c,doc):
        c.saveState()
        c.setFont('Times-Roman',9)
        c.setFillColorRGB(0.5,0.5,0.5)
        #c.drawString(1*cm,self._PAGE_HEIGHT-1*cm,
        #    "%s / %s"%(escape(self._conf.getTitle()),self._title))
        #c.drawCentredString(self._PAGE_WIDTH/2.0,0.5*cm,"Page %d "%doc.page)
        self._drawWrappedString(c, self._track.getTitle())
        c.setFont('Times-Roman',9)
        c.setFillColorRGB(0.5,0.5,0.5)
        c.restoreState()

    def laterPages(self,c,doc):
        c.saveState()
        c.setFont('Times-Roman',9)
        c.setFillColorRGB(0.5,0.5,0.5)
        #c.drawString(1*cm,self._PAGE_HEIGHT-1*cm,
        #    "%s / %s"%(escape(self._conf.getTitle()),self._title))
        #c.drawCentredString(self._PAGE_WIDTH/2.0,0.5*cm,"Page %d "%doc.page)
        c.restoreState()

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story
        self._story.append(PageBreak())
        self._story.append(PageBreak())
        return story

class RegistrantToPDF(PDFBase):

    def __init__(self, conf, reg, display, doc=None, story=None):
        self._reg = reg
        self._conf = conf
        self._display = display
        if not story:
            story = [Spacer(inch, 5*cm)]
        PDFBase.__init__(self, doc, story)
        self._title = _("Registrant")
        self._PAGE_HEIGHT = defaultPageSize[1]
        self._PAGE_WIDTH = defaultPageSize[0]

    def firstPage(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 25)
        #c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT - inch - 5*cm, self._abstract.getTitle())
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        #c.drawString(0.5*inch, 0.5*inch, Config.getInstance().getBaseURL())
        c.restoreState()

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story

        style = ParagraphStyle({})
        style.fontSize = 12
        text = i18nformat(""" _("Registrant ID") : %s""")%self._reg.getId()
        p = Paragraph(text, style, part=escape(self._reg.getFullName()))
        story.append(p)

        story.append(Spacer(inch, 0.5*cm, part=escape(self._reg.getFullName())))

        style = ParagraphStyle({})
        style.alignment = TA_CENTER
        style.fontSize = 25
        style.leading = 30
        text = escape(self._reg.getFullName())
        p = Paragraph(text, style, part=escape(self._reg.getFullName()))
        story.append(p)

        indexedFlowable[p] = {"text":escape(self._reg.getFullName()), "level":1}
        story.append(Spacer(inch, 1*cm, part=escape(self._reg.getFullName())))
        style = ParagraphStyle({})
        style.alignment = TA_JUSTIFY
        for key in self._display:
            text = ""
            if key == "Email" and self._reg.getEmail() <> "":
                text = i18nformat("""<b> _("Email")</b>: %s""")%escape(self._reg.getEmail())
            elif key == "Position" and self._reg.getPosition() <> "":
                text = i18nformat("""<b> _("Position")</b>: %s""")%escape(self._reg.getPosition())
            elif key == "LastName" and self._reg.getFamilyName() <> "":
                text = i18nformat("""<b> _("Surname")</b>: %s""")%escape(self._reg.getFamilyName())
            elif key == "FirstName" and self._reg.getFirstName() <> "":
                text = i18nformat("""<b> _("First Name")</b>: %s""")%escape(self._reg.getFirstName())
            elif key == "Institution" and self._reg.getInstitution() <> "":
                text = i18nformat("""<b> _("Institution")</b>: %s""")%escape(self._reg.getInstitution())
            elif key == "Address" and self._reg.getAddress() <> "":
                text = i18nformat("""<b> _("Address")</b>: %s""")%escape(self._reg.getAddress())
            elif key == "City" and self._reg.getCity() <> "":
                text = i18nformat("""<b> _("City")</b>:  %s""")%escape(self._reg.getCity())
            elif key == "Country" and self._reg.getCountry() <> "":
                text = i18nformat("""<b> _("Country")</b>: %s""")%escape(CountryHolder().getCountryById(self._reg.getCountry()))
            elif key == "Phone" and self._reg.getPhone() <> "":
                text = i18nformat("""<b> _("Phone")</b>: %s""")%escape(self._reg.getPhone())
            elif key == "isPayed" and self._reg.isPayedText() <> "":
                text = i18nformat("""<b> _("Paid")</b>: %s""")%escape(self._reg.isPayedText())
            elif key == "idpayment" and self._reg.getIdPay() <> "":
                text = i18nformat("""<b> _("idpayment")</b>: %s""")%escape(self._reg.getIdPay())
            elif key == "amountToPay":
                text = i18nformat("""<b> _("Amount")</b>: %.2f %s""")%(self._reg.getTotal(), escape(self._reg.getConference().getRegistrationForm().getCurrency()))
            elif key == "Sessions":
                listSession = []
                for ses in self._reg.getSessionList():
                    if ses is not None:
                        listSession.append("%s"%escape(ses.getTitle()))
                if len(listSession) > 0:
                    text = i18nformat("""<b> _("Sessions")</b>: """)
                    text += " ; ".join(listSession)
            elif key == "SocialEvents":
                listSocialEvents = []
                for se in self._reg.getSocialEvents():
                    if se is not None:
                        listSocialEvents.append("%s"%escape(se.getCaption()))
                if len(listSocialEvents) > 0:
                    text = i18nformat("""<b> _("Social Events")</b>: """)
                    text += " ; ".join(listSocialEvents)
            elif key == "Accommodation" and self._reg.getAccommodation() is not None and \
            self._reg.getAccommodation().getAccommodationType() is not None:
                text = i18nformat("""<b> _("Acommodation")</b>: %s""") % escape(self._reg.getAccommodation().getAccommodationType().getCaption())
            elif key == "ArrivalDate" and self._reg.getAccommodation() is not None and \
            self._reg.getAccommodation().getArrivalDate() is not None:
                text = i18nformat("""<b> _("Arrival Date")</b>: %s""") % escape(self._reg.getAccommodation().getArrivalDate().strftime("%d-%B-%Y"))
            elif key == "DepartureDate" and self._reg.getAccommodation() is not None and \
            self._reg.getAccommodation().getDepartureDate() is not None:
                text = i18nformat("""<b> _("Departure Date")</b>: %s""") % escape(self._reg.getAccommodation().getDepartureDate().strftime("%d-%B-%Y"))
            elif key == "ReasonParticipation" and self._reg.getReasonParticipation() is not None and \
            self._reg.getReasonParticipation() is not None and self._reg.getReasonParticipation() != "":
                text = i18nformat("""<b> _("Reason Participation")</b>: %s""") % escape(self._reg.getReasonParticipation())
            elif key == "RegistrationDate" and self._reg.getRegistrationDate() is not None:
                text = i18nformat("""<b> _("Registration date")</b>: %s""") % escape(self._reg.getAdjustedRegistrationDate().strftime("%d-%B-%Y-%H:%M"))

            elif key.startswith("s-"):
                ids = key.split("-")
                if len(ids) == 2:
                    status = self._reg.getStatusById(ids[1])
                    if status.getStatusValue() is not None:
                        text = _("""<b> %s</b>: %s""") % (escape(status.getCaption()), escape(status.getStatusValue().getCaption()))
            else:
                ids = key.split("-")
                if len(ids) == 2:
                    group = self._reg.getMiscellaneousGroupById(ids[0])
                    if group is not None:
                        field = self._conf.getRegistrationForm().getSectionById(ids[0]).getFieldById(ids[1])
                        response = group.getResponseItemById(ids[1])
                        if response is not None and response.getValue() != "":
                            text = _("""<b> %s</b>: %s""") % (escape(field.getCaption()), escape(str(response.getValue())))
            if text != "":
                p = Paragraph(text, style,  part=escape(self._reg.getFullName()))
                story.append(p)
                story.append(Spacer(inch, 0.2*cm, part=escape(self._reg.getFullName())))
        return story

class RegistrantsListToBookPDF(PDFWithTOC):
    def __init__(self, conf,doc=None, story=[],list=None, display=["Institution", "Phone", "City", "Country"]):
        self._conf = conf
        self._regForm = conf.getRegistrationForm()
        self._regList = list
        self._display = display
        self._title = _("Registrants Book")
        PDFWithTOC.__init__(self)

    def firstPage(self, c, doc):
        c.saveState()
        showLogo = False
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 35)
        c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT/2, self._title)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        c.drawString(0.5*inch, 0.5*inch, str(urlHandlers.UHConferenceDisplay.getURL(self._conf)))
        c.restoreState()

    def laterPages(self, c, doc):

        c.saveState()
        c.setFont('Times-Roman', 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        confTitle = escape(self._conf.getTitle())
        if len(self._conf.getTitle())>30:
            confTitle = escape(self._conf.getTitle()[:30] + "...")
        c.drawString(inch, self._PAGE_HEIGHT - 0.75 * inch, "%s / %s"%(confTitle, self._title))
        title = doc.getCurrentPart()
        if len(doc.getCurrentPart())>50:
            title = utils.unicodeSlice(doc.getCurrentPart(), 0, 50) + "..."
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, "%s"%title)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, i18nformat(""" _("Page") %d """)%doc.page)
        c.drawString(inch,  0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()


    def getBody(self):
        for reg in self._regList:
            temp = RegistrantToPDF(self._conf, reg, self._display)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())


class RegistrantsListToPDF(PDFBase):

    def __init__(self, conf,doc=None, story=[],list=None, display=["Institution", "Phone", "City", "Country"]):
        self._conf = conf
        self._regForm = conf.getRegistrationForm()
        self._regList = list
        self._display = display
        PDFBase.__init__(self, doc, story, printLandscape=True)
        self._title = _("Registrants List")
        self._PAGE_HEIGHT = landscape(A4)[1]
        self._PAGE_WIDTH = landscape(A4)[0]

    def firstPage(self, c, doc):
        c.saveState()
        showLogo = False
        c.setFont('Times-Bold', 30)
        if not showLogo:
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT-0.75*inch)
        c.setFont('Times-Bold', 25)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        c.setFont('Times-Roman', 10)
        c.drawRightString(self._PAGE_WIDTH - inch,self._PAGE_HEIGHT-1*cm, "%s"%(nowutc().strftime("%d %B %Y, %H:%M")))
        c.restoreState()

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story

        style = ParagraphStyle({})
        style.fontSize = 12
        style.alignment = TA_CENTER
        text = i18nformat("""<b>_("List of registrants")</b>""")
        p = Paragraph(text, style, part=escape(self._conf.getTitle()))
        p.spaceAfter = 30
        story.append(p)

        styleRegistrant = ParagraphStyle({})
        styleRegistrant.leading = 10
        styleRegistrant.fontName = "Times-Roman"
        styleRegistrant.fontSize = 8
        styleRegistrant.spaceBefore=0
        styleRegistrant.spaceAfter=0
        styleRegistrant.alignment=TA_LEFT
        styleRegistrant.leftIndent=10
        styleRegistrant.firstLineIndent=0

        tsRegs=TableStyle([('VALIGN',(0,0),(-1,-1),"MIDDLE"),
                        ('LINEBELOW',(0,0),(-1,0), 1, colors.black),
                        ('ALIGN',(0,0),(-1,0),"CENTER"),
                        ('ALIGN',(0,1),(-1,-1),"LEFT") ] )
        l = []
        lp = []
        lp.append(Paragraph( i18nformat("""<b> _("Name")</b>"""), styleRegistrant))

        for key in self._display:
            if key in ["Email", "Position", "LastName", "FirstName", "Institution", "Phone", "City", "Country", "Address", "RegistrationDate"]:
                p=Paragraph("""<b>%s</b>"""%key, styleRegistrant)
            elif key=="Accommodation":
                p=Paragraph("""<b>%s</b>"""%escape(self._regForm.getAccommodationForm().getTitle()), styleRegistrant)
            elif key == "SocialEvents":
                p=Paragraph("""<b>%s</b>"""%escape(self._regForm.getSocialEventForm().getTitle()), styleRegistrant)
            elif key == "Sessions":
                p=Paragraph("""<b>%s</b>"""%escape(self._regForm.getSessionsForm().getTitle()), styleRegistrant)
            elif key=="ArrivalDate":
                p=Paragraph( i18nformat("""<b> _("Arrival Date")</b>"""), styleRegistrant)
            elif key=="DepartureDate":
                p=Paragraph( i18nformat("""<b> _("Departure Date")</b>"""), styleRegistrant)
            elif key == "ReasonParticipation":
                p=Paragraph("""<b>%s</b>"""%escape(self._regForm.getReasonParticipationForm().getTitle()), styleRegistrant)
            elif key == "isPayed":
                p=Paragraph("""<b>Paid</b>""", styleRegistrant)
            elif key == "idpayment":
                p=Paragraph("""<b>Payment ID</b>""", styleRegistrant)
            elif key == "amountToPay":
                p=Paragraph("""<b>Amount</b>""", styleRegistrant)
            elif key.startswith("s-"):
                ids=key.split("-")
                if len(ids)==2:
                    status=self._regForm.getStatusById(ids[1])
                    p=Paragraph("""<b>%s</b>"""%escape(status.getCaption()), styleRegistrant)
                else:
                    p=Paragraph("", styleRegistrant)
            else:
                ids=key.split("-")
                if len(ids)==2:
                    group=self._regForm.getSectionById(ids[0])
                    if group is not None:
                        i=group.getFieldById(ids[1])
                        if i is not None:
                            p=Paragraph("""<b>%s</b>"""%escape(i.getCaption()), styleRegistrant)
            lp.append(p)
        l.append(lp)

        if self._regList == None:
            self._regList = self._conf.getRegistrantsList(True)
        for reg in self._regList:
            lp = []
            lp.append(Paragraph("""%s"""%escape(reg.getFullName()), styleRegistrant))
            for key in self._display:
                if key == "Email":
                    lp.append(Paragraph("""%s"""%escape(reg.getEmail()), styleRegistrant))
                elif key == "Position":
                    lp.append(Paragraph("""%s"""%escape(reg.getPosition()), styleRegistrant))
                elif key == "LastName":
                    lp.append(Paragraph("""%s"""%escape(reg.getFamilyName()), styleRegistrant))
                elif key == "FirstName":
                    lp.append(Paragraph("""%s"""%escape(reg.getFirstName()), styleRegistrant))
                elif key == "Institution":
                    lp.append(Paragraph("""%s"""%escape(reg.getInstitution()), styleRegistrant))
                elif key == "Address":
                    lp.append(Paragraph("""%s"""%escape(reg.getAddress()), styleRegistrant))
                elif key == "City":
                    lp.append(Paragraph("""%s"""%escape(reg.getCity()), styleRegistrant))
                elif key == "Country":
                    lp.append(Paragraph("""%s"""%CountryHolder().getCountryById(reg.getCountry()), styleRegistrant))
                elif key == "Phone":
                    lp.append(Paragraph("""%s"""%escape(reg.getPhone()), styleRegistrant))
                elif key == "isPayed":
                    lp.append(Paragraph("""%s"""%escape(reg.isPayedText()), styleRegistrant))
                elif key == "idpayment":
                    lp.append(Paragraph("""%s"""%escape(reg.getIdPay()), styleRegistrant))
                elif key == "amountToPay":
                    lp.append(Paragraph("%.2f %s"%(reg.getTotal(), reg.getConference().getRegistrationForm().getCurrency()), styleRegistrant))
                elif key == "Sessions":
                    p7 = []
                    for ses in reg.getSessionList():
                        if ses is not None:
                            p7.append(Paragraph("""%s"""%escape(ses.getTitle()), styleRegistrant))
                    if p7 == []:
                        p7 = Paragraph("", styleRegistrant)
                    lp.append(p7)
                elif key == "SocialEvents":
                    p8 = []
                    for se in reg.getSocialEvents():
                        if se is not None:
                            p8.append(Paragraph("""%s"""%escape(se.getCaption()), styleRegistrant))
                    if p8 == []:
                        p8 = Paragraph("", styleRegistrant)
                    lp.append(p8)
                elif key == "Accommodation":
                    if reg.getAccommodation() is not None and reg.getAccommodation().getAccommodationType() is not None:
                        lp.append(Paragraph("%s"%escape(reg.getAccommodation().getAccommodationType().getCaption()), styleRegistrant))
                    else:
                        lp.append(Paragraph("", styleRegistrant))
                elif key == "ArrivalDate":
                    if reg.getAccommodation() is not None and reg.getAccommodation().getArrivalDate() is not None:
                        lp.append(Paragraph("%s"%escape(reg.getAccommodation().getArrivalDate().strftime("%d-%B-%Y")), styleRegistrant))
                    else:
                        lp.append(Paragraph("", styleRegistrant))
                elif key == "DepartureDate":
                    if reg.getAccommodation() is not None and reg.getAccommodation().getDepartureDate() is not None:
                        lp.append(Paragraph("%s"%escape(reg.getAccommodation().getDepartureDate().strftime("%d-%B-%Y")), styleRegistrant))
                    else:
                        lp.append(Paragraph("", styleRegistrant))
                elif key == "ReasonParticipation":
                    lp.append(Paragraph("""%s"""%escape(reg.getReasonParticipation() or ""), styleRegistrant))
                elif key == "RegistrationDate":
                    if reg.getRegistrationDate() is not None:
                        lp.append(Paragraph("""%s"""%escape(reg.getAdjustedRegistrationDate().strftime("%d-%B-%Y-%H:%M")), styleRegistrant))
                    else:
                        lp.append(Paragraph("", styleRegistrant))
                elif key.startswith("s-"):
                    ids=key.split("-")
                    if len(ids)==2:
                        status=reg.getStatusById(ids[1])
                        cap=""
                        if status.getStatusValue() is not None:
                            cap=status.getStatusValue().getCaption()
                        lp.append(Paragraph("""%s"""%escape(cap), styleRegistrant))
                else:
                    ids=key.split("-")
                    if len(ids)==2:
                        group=reg.getMiscellaneousGroupById(ids[0])
                        if group is not None:
                            i=group.getResponseItemById(ids[1])
                            if i is not None:
                                lp.append(Paragraph("""%s"""%escape(str(i.getValue())), styleRegistrant))
                                continue
                    lp.append(Paragraph("", styleRegistrant))
            l.append(lp)
        noneList = ()
        for i in range(0, len(self._display)+1):
            noneList += (None,)
        t=Table(l,colWidths=noneList,style=tsRegs)
        self._story.append(t)
        return story


class RegistrantsListToBadgesPDF:
    """
    Class used to print the Badges for the registrants
    """

    """
    The following dictionary maps the names of the fonts, as returned by the javascript in WConfModifBadgeDesign.tpl,
    to actual TTF font names.
    Each font name is mapped to 4 TTF fonts: Normal one, Bold one, Italic one, Bold & Italic one.
    """
    __fonts = {'Times New Roman':['Times-Roman','Times-Bold','Times-Italic','Times-Bold-Italic'],
               'Courier':['Courier', 'Courier-Bold', 'Courier-Italic', 'Courier-Bold-Italic'],
               'Sans':['Sans', 'Sans-Bold', 'Sans-Italic', 'Sans-Bold-Italic'],
               'LinuxLibertine':['LinuxLibertine','LinuxLibertine-Bold','LinuxLibertine-Italic','LinuxLibertine-Bold-Italic'],
               'Kochi-Mincho':['Kochi-Mincho','Kochi-Mincho','Kochi-Mincho','Kochi-Mincho'],
               'Kochi-Gothic':['Kochi-Gothic','Kochi-Gothic','Kochi-Gothic','Kochi-Gothic'],
               'Uming-CN':['Uming-CN','Uming-CN','Uming-CN','Uming-CN']
           #,'Bitstream Cyberbit':['Bitstream-Cyberbit', 'Bitstream-Cyberbit', 'Bitstream-Cyberbit', 'Bitstream-Cyberbit']
               }

    """ The following dictionary maps the sizes of the items, as returned by the javascript in WConfModifBadgeDesign.tpl,
    to actual font sizes in points, as ReportLab needs.
    """
    __fontSizes = {'xx-small':9,
                   'x-small':10,
                   'small':11,
                   'medium':12,
                   'large':14,
                   'x-large':16,
                   'xx-large':24
                   }

    """ The following dictionary maps the possible text alignments, as returned by the javascript in WConfModifBadgeDesign.tpl,
    to ReportLab constants.
    """
    __alignments = {'Left':TA_LEFT,
                    'Right':TA_RIGHT,
                    'Center':TA_CENTER,
                    'Justified':TA_JUSTIFY
                    }

    """ The following dictionary maps the possible text colors, as returned by the javascript in WConfModifBadgeDesign.tpl,
    to ReportLab color constants.
    """
    __colors = {'black': colors.black,
                'red': colors.red,
                'blue': colors.blue,
                'green': colors.green,
                'yellow': colors.yellow,
                'brown': colors.brown,
                'cyan': colors.cyan,
                'gold': colors.gold,
                'pink': colors.pink,
                'gray': colors.gray,
                'white': colors.white
                }


    def __init__(self, conf, badgeTemplate, marginTop, marginBottom, marginLeft, marginRight, marginColumns, marginRows, pagesize, drawDashedRectangles, registrantList):
        """ Constructor
                conf: the conference for which the badges are printed, as a Conference object.
                badgeTemplate: the template used, as a BadgeTemplate object.
                marginTop: a float indicating the top margin, in cm, int or float
                marginBottom: a float indicating the minimum bottom margin, in cm, int or float
                marginLeft: a float indicating the left margin, in cm, int or float
                marginRight: a float indicating the minimum right margin, in cm, int or float
                marginColumns: a float indicating the margin between columns of badges, in cm, int or float
                marginRows: a float indicating the margin between rows of badges, in cm, int or float
                pagesize: a string with the pagesize to used, e.g. 'A4', 'A3', 'Letter'
                registrantList: either a string whose value should be "all", either a list of registrant id's
            The badges will be drawn aligned to the left.
        """

        self.__conf = conf
        self.__badgeTemplate = badgeTemplate
        self.__marginTop = marginTop
        self.__marginBottom = marginBottom
        self.__marginLeft = marginLeft
        self.__marginRight = marginRight
        self.__marginColumns = marginColumns
        self.__marginRows = marginRows

        if registrantList == 'all':
            self.__registrantList = self.__conf.getRegistrantsList(sort = True)
        else:
            self.__registrantList = [self.__conf.getRegistrantById(id) for id in registrantList]

        self.__size = PDFSizes().PDFpagesizes[pagesize]
        self.__width, self.__height = self.__size

        self.__drawDashedRectangles = drawDashedRectangles

        setTTFonts()


    def getPDFBin(self):
        """ Returns the data of the PDF file to be printed
        """

        self.__fileDummy = FileDummy()
        self.__canvas = canvas.Canvas(self.__fileDummy, pagesize = self.__size)

        nBadgesHorizontal = int((self.__width - self.__marginLeft * cm - self.__marginRight * cm + self.__marginColumns * cm  + 0.01*cm) /
                                ((self.__badgeTemplate.getWidthInCm() + self.__marginColumns)  * cm))


        nBadgesVertical = int((self.__height - self.__marginTop * cm - self.__marginBottom * cm + self.__marginRows * cm + 0.01*cm) /
                              ((self.__badgeTemplate.getHeightInCm() + self.__marginRows) * cm))

        # We get an instance of the position generator
        p = RegistrantsListToBadgesPDF.__position_generator(
                               nBadgesHorizontal, nBadgesVertical,
                               self.__badgeTemplate.getWidthInCm() * cm, self.__badgeTemplate.getHeightInCm() * cm,
                               self.__marginLeft * cm, self.__marginTop * cm, self.__marginColumns * cm, self.__marginRows * cm)

        if nBadgesHorizontal == 0 or nBadgesVertical == 0:
            raise NoReportError( _("The template dimensions are too large for the page size you selected"))

        # We print a badge for each registrant
        for registrant in self.__registrantList:
            try:
                posx, posy = p.next()
                self.__draw_badge(registrant, posx, posy)
            except StopIteration:
                # We have printed all the badges that fitted in 1 page, we have to restart the position generator.
                self.__canvas.showPage()
                p = RegistrantsListToBadgesPDF.__position_generator(
                               nBadgesHorizontal, nBadgesVertical,
                               self.__badgeTemplate.getWidthInCm() * cm, self.__badgeTemplate.getHeightInCm() * cm,
                               self.__marginLeft * cm, self.__marginTop * cm, self.__marginColumns * cm, self.__marginRows * cm)
                posx, posy = p.next()
                self.__draw_badge(registrant, posx, posy)

        self.__canvas.save()
        return self.__fileDummy.getData()

    def __position_generator(cls,
                             nBadgesHorizontal, nBadgesVertical,
                             badgeWidth, badgeHeight,
                             marginLeft, marginTop,
                             interColumnMargin, interRowMargin):
        """ Generates the a new position for drawing a badge each time it is called.
        The position of a badge is the position of the top left corner.
        When there are no more positions available in a page, it throws a StopIteration exception.
        """

        nx = 0
        ny = 0
        while ny < nBadgesVertical:
            while nx < nBadgesHorizontal:
                x = marginLeft + nx * (badgeWidth + interColumnMargin)
                y = marginTop + ny * (badgeHeight + interRowMargin)
                nx = nx + 1
                yield x,y
            nx = 0
            ny = ny + 1
        return
    __position_generator = classmethod(__position_generator)


    def __draw_badge(self, registrant, posx, posy):
        """ Draws a badge, for a given registrant, at the position (posx, posy).
        (posx, posy) is the position of the top left corner of a badge.
        """

        # We draw a dashed rectangle around the badge
        if self.__drawDashedRectangles:
            self.__canvas.saveState()
            self.__canvas.setDash(1,5)
            self.__canvas.rect(posx, self.__height - posy - self.__badgeTemplate.getHeightInCm() * cm,
                               self.__badgeTemplate.getWidthInCm() * cm, self.__badgeTemplate.getHeightInCm() * cm)
            self.__canvas.restoreState()

        # We draw the background if we find it.
        usedBackgroundId = self.__badgeTemplate.getUsedBackgroundId()
        if usedBackgroundId != -1 and self.__badgeTemplate.getBackground(usedBackgroundId)[1] is not None:
            self.__canvas.drawImage(self.__badgeTemplate.getBackground(usedBackgroundId)[1].getFilePath(),
                                    posx, self.__height - posy - self.__badgeTemplate.getHeightInCm() * cm,
                                    self.__badgeTemplate.getWidthInCm() * cm, self.__badgeTemplate.getHeightInCm() * cm)


        # We draw the items of the badge
        for item in self.__badgeTemplate.getItems():
            # First we determine the actual text that has to be drawed.
            action = BadgeDesignConfiguration().items_actions[item.getKey()][1]
            if isinstance(action, str):
                # If for this kind of item we have to draw always the same string, let's draw it.
                text = action
            elif isinstance(action, types.MethodType):
                # If the action is a method, depending on which class owns the method, we pass a
                # different object to the method.
                if action.im_class == Registrant:
                    text = action.__call__(registrant)
                elif action.im_class == conference.Conference:
                    text = action.__call__(self.__conf)
                elif action.im_class == BadgeTemplateItem:
                    text = action.__call__(item)
                else:
                    text= _("Error")
            elif isinstance(action, types.ClassType):
                # If the action is a class, it must be a class who complies to the following interface:
                #  -it must have a getArgumentType() method, which returns either Conference, Registrant or BadgeTemplateItem.
                #  Depending on what is returned, we will pass a different object to the getValue() method.
                #  -it must have a getValue(object) method, to which a Conference instance, a Registrant instance or a
                #  BadgeTemplateItem instance must be passed, depending on the result of the getArgumentType() method.
                argumentType = action.getArgumentType()
                if argumentType == Registrant:
                    text = action.getValue(registrant)
                elif argumentType == conference.Conference:
                    text = action.getValue(self.__conf)
                elif argumentType == BadgeTemplateItem:
                    text = action.getValue(item)
                else:
                    text = _("Error")
            else:
                text = _("Error")

            if not isinstance(text, basestring):
                text = str(text)
            text = escape(text)

            #style definition for the Paragraph used to draw the text.
            style = ParagraphStyle({})
            style.alignment = RegistrantsListToBadgesPDF.__alignments[item.getTextAlign()]
            style.textColor = RegistrantsListToBadgesPDF.__colors[item.getColor()]
            style.fontSize = RegistrantsListToBadgesPDF.__fontSizes.get(item.getFontSize(), 25)
            style.leading = style.fontSize

            if item.isBold() and item.isItalic():
                style.fontName = style.fontName = RegistrantsListToBadgesPDF.__fonts[item.getFont()][3]
            elif item.isItalic():
                style.fontName = style.fontName = RegistrantsListToBadgesPDF.__fonts[item.getFont()][2]
            elif item.isBold():
                style.fontName = style.fontName = RegistrantsListToBadgesPDF.__fonts[item.getFont()][1]
            else:
                style.fontName = style.fontName = RegistrantsListToBadgesPDF.__fonts[item.getFont()][0]

            p = Paragraph(text, style)

            itemx = self.__badgeTemplate.pixelsToCm(item.getX()) * cm
            itemy = self.__badgeTemplate.pixelsToCm(item.getY()) * cm

            availableWidth = self.__badgeTemplate.pixelsToCm(item.getWidth()) * cm
            availableHeight = (self.__badgeTemplate.getHeightInCm()
                               - self.__badgeTemplate.pixelsToCm(item.getY()) \
                              ) * cm

            w,h = p.wrap(availableWidth, availableHeight)

            if w > availableWidth or h > availableHeight:
                ## TODO: give warnings
                pass

            p.drawOn(self.__canvas, posx + itemx, self.__height - posy - itemy - h)


class LectureToPosterPDF:
    """
    Class used to print a lecture's poster
    """

    """ The following dictionary maps the names of the fonts, as returned by the javascript in WConfModifPosterDesign.tpl,
    to actual TTF font names.
    Each font name is mapped to 4 TTF fonts: Normal one, Bold one, Italic one, Bold & Italic one.
    """
    __fonts = {'Times New Roman':['Times-Roman','Times-Bold','Times-Italic','Times-Bold-Italic'],
               'Courier':['Courier', 'Courier-Bold', 'Courier-Italic', 'Courier-Bold-Italic'],
               'Sans':['Sans', 'Sans-Bold', 'Sans-Italic', 'Sans-Bold-Italic'],
               'LinuxLibertine':['LinuxLibertine','LinuxLibertine-Bold','LinuxLibertine-Italic','LinuxLibertine-Bold-Italic'],
               'Kochi-Mincho':['Kochi-Mincho','Kochi-Mincho','Kochi-Mincho','Kochi-Mincho'],
               'Kochi-Gothic':['Kochi-Gothic','Kochi-Gothic','Kochi-Gothic','Kochi-Gothic'],
               'Uming-CN':['Uming-CN','Uming-CN','Uming-CN','Uming-CN']
           #,'Bitstream Cyberbit':['Bitstream-Cyberbit', 'Bitstream-Cyberbit', 'Bitstream-Cyberbit', 'Bitstream-Cyberbit']
               }


    """ The following dictionary maps the possible text alignments, as returned by the javascript in WConfModifPosterDesign.tpl,
    to ReportLab constants.
    """
    __alignments = {'Left':TA_LEFT,
                    'Right':TA_RIGHT,
                    'Center':TA_CENTER,
                    'Justified':TA_JUSTIFY
                    }

    """ The following dictionary maps the possible text colors, as returned by the javascript in WConfModifPosterDesign.tpl,
    to ReportLab color constants.
    """
    __colors = {'black': colors.black,
                'red': colors.red,
                'blue': colors.blue,
                'green': colors.green,
                'yellow': colors.yellow,
                'brown': colors.brown,
                'cyan': colors.cyan,
                'gold': colors.gold,
                'pink': colors.pink,
                'gray': colors.gray,
                'white': colors.white
                }


    def __init__(self, conf, posterTemplate, marginH, marginV, pagesize, tz=None):
        """ Constructor
        conf: the conference for which the posters are printed, as a Conference object.
        posterTemplate: the template used, as a PosterTemplate object.
        marginH: a number indicating the minimal horizontal margin
        marginV: a number indicating the minimal vertical margin
        pagesize: a string with the pagesize to used, e.g. 'A4', 'A3', 'Letter'
        registrantList: either a string whose value should be "all",
                        either a list of registrant id's
        """

        self.__conf = conf
        if not tz:
            self._tz = self.__conf.getTimezone()
        else:
            self._tz = tz
        self.__posterTemplate = posterTemplate
        self.__marginH = marginH
        self.__marginV = marginV

        self.__size = PDFSizes().PDFpagesizes[pagesize]
        self.__width, self.__height = self.__size

        setTTFonts()

    """ The following function maps the sizes of the items, as returned by the javascript in WConfModifPosterDesign.tpl,
    to actual font sizes in points, as ReportLab needs.
    """
    def __extract_size(cls, sizePt):

        m = re.match(r"(\d+)(pt)",sizePt)

        if m:
            return int(m.group(1))
        return None
    __extract_size = classmethod (__extract_size)


    def getPDFBin(self):
        """ Returns the data of the PDF file to be printed
        """

        self.__fileDummy = FileDummy()
        self.__canvas = canvas.Canvas(self.__fileDummy, pagesize = self.__size)

        self.__draw_poster(self.__marginH * cm, self.__marginV * cm)

        self.__canvas.save()
        return self.__fileDummy.getData()

    def __draw_background(self, file, position, posx, posy):

        img = Image.open(file)

        imgWidth, imgHeight = img.size

        posx = self.__posterTemplate.pixelsToCm(posx);
        posy = self.__posterTemplate.pixelsToCm(posy);

        if position == "Stretch":
            x_1 = posx
            y_1 = posy
            width = self.__posterTemplate.getWidthInCm()
            height = self.__posterTemplate.getHeightInCm()

        elif position == "Center":
            height = self.__posterTemplate.pixelsToCm(imgHeight)
            width = self.__posterTemplate.pixelsToCm(imgWidth)

            posterWidth = self.__posterTemplate.getWidthInCm()
            posterHeight = self.__posterTemplate.getHeightInCm()

            if width > posterWidth or height > posterHeight:

                if width > posterWidth:
                    ratio = float(posterWidth)/width;
                    width = posterWidth;
                    height = height*ratio

                    x_1 = posx;
                    y_1 = posy + (posterHeight - height)/2.0;


                if  height > posterHeight:
                    ratio = float(posterHeight)/height;
                    height = posterHeight;
                    width = width*ratio
                    x_1 = posx + (posterWidth - width)/2.0;
                    y_1 = posy;
            else:
                x_1 = posx + (posterWidth - self.__posterTemplate.pixelsToCm(imgWidth))/2.0
                y_1 = posy + (posterHeight - self.__posterTemplate.pixelsToCm(imgHeight))/2.0

        self.__canvas.drawImage(file,
                                x_1 * cm, y_1 * cm,
                                width * cm, height * cm)


    def __draw_poster(self, posx, posy):
        """ Draws a poster, for a given registrant, at the position (posx, posy).
        (posx, posy) is the position of the top left corner of a poster.
        """

        # We draw the background if we find it.
        usedBackgroundId = self.__posterTemplate.getUsedBackgroundId()

        if usedBackgroundId != -1 and self.__posterTemplate.getBackground(usedBackgroundId)[1] is not None:

            self.__draw_background(self.__posterTemplate.getBackground(usedBackgroundId)[1].getFilePath(),
                             self.__posterTemplate.getBackgroundPosition(usedBackgroundId),posx,posy)

        # We draw the items of the poster
        for item in self.__posterTemplate.getItems():

            # First we determine the actual text that has to be drawed.
            action = PosterDesignConfiguration().items_actions[item.getKey()][1]

            if isinstance(action, str):
                # If for this kind of item we have to draw always the same string, let's draw it.
                # text is passed in lists, because some fields need several lines
                text = [action]
            elif isinstance(action, types.MethodType):
                # If the action is a method, depending on which class owns the method, we pass a
                # different object to the method.
                if action.im_class == conference.Conference:
                    text = action.__call__(self.__conf).replace("\r\n","\n").split("\n")
                elif action.im_class == PosterTemplateItem:
                    text = [action.__call__(item)]
                else:
                    text= [_("Error")]
            elif isinstance(action, types.ClassType):
                # If the action is a class, it must be a class who complies to the following interface:
                #  -it must have a getArgumentType() method, which returns either Conference or PosterTemplateItem.
                #  Depending on what is returned, we will pass a different object to the getValue() method.
                #  -it must have a getValue(object) method, to which a Conference instance or a
                #  PosterTemplateItem instance must be passed, depending on the result of the getArgumentType() method.
                argumentType = action.getArgumentType()
                if action.__name__ == "ConferenceChairperson":
                    #this specific case may need more than one line
                    chairList = action.getValue(self.__conf)

                    # 'text' is a list of lines
                    text = []
                    # let's fill it with the chairpersons' names
                    for chair in chairList:
                        if chair.getAffiliation() != "":
                            text.append("%s (%s)" % (chair.getDirectFullName(),chair.getAffiliation()))
                        else:
                            text.append(chair.getDirectFullName())

                elif argumentType == conference.Conference:
                    text = [action.getValue(self.__conf)]
                elif argumentType == PosterTemplateItem:
                    text = [action.getValue(item)]
                else:
                    text = [_("Error")]
            else:
                text = [_("Error")]

            text = map(escape,text)

            #style definition for the Paragraph used to draw the text.
            style = ParagraphStyle({})
            style.alignment = LectureToPosterPDF.__alignments[item.getTextAlign()]
            style.textColor = LectureToPosterPDF.__colors[item.getColor()]
            style.fontSize = LectureToPosterPDF.__extract_size(item.getFontSize())
            style.leading = style.fontSize

            if item.isBold() and item.isItalic():
                style.fontName = style.fontName = LectureToPosterPDF.__fonts[item.getFont()][3]
            elif item.isItalic():
                style.fontName = style.fontName = LectureToPosterPDF.__fonts[item.getFont()][2]
            elif item.isBold():
                style.fontName = style.fontName = LectureToPosterPDF.__fonts[item.getFont()][1]
            else:
                style.fontName = style.fontName = LectureToPosterPDF.__fonts[item.getFont()][0]

            availableWidth = self.__posterTemplate.pixelsToCm(item.getWidth()) * cm
            availableHeight = (self.__posterTemplate.getHeightInCm()
                               - self.__posterTemplate.pixelsToCm(item.getY()) \
                              ) * cm

            w,h = 0,0
            itemx = self.__posterTemplate.pixelsToCm(item.getX()) * cm
            itemy = self.__posterTemplate.pixelsToCm(item.getY()) * cm

            # now, we iterate over the line set
            for line in text:
                if line == "":
                    itemy += style.fontSize
                else:
                    p = Paragraph(line, style)

                    itemy += h

                    w,h = p.wrap(availableWidth, availableHeight)

                    if w > availableWidth or h > availableHeight:
                        ## TODO: warnings
                        pass

                    # finally, draw
                    p.drawOn(self.__canvas, posx + itemx, self.__height - posy - itemy - h)


class TicketToPDF(PDFBase):

    def __init__(self, conf, registrant, doc=None, story=None):
        self._conf = conf
        self._registrant = registrant
        PDFBase.__init__(self, doc, story)

    def firstPage(self, c, doc):
        c.saveState()
        height = self._PAGE_HEIGHT - 1*cm
        width = 1*cm

        # Conference title
        height -= 1*cm
        self._drawWrappedString(c, escape(self._conf.getTitle()),
                                height=height, width=width, size=20,
                                align="left", font='Times-Bold')

        # Conference start and end date
        height -= 0.7*cm
        self._drawWrappedString(c, "%s - %s" % (
            format_date(self._conf.getStartDate(), format='full'),
            format_date(self._conf.getEndDate(), format='full')),
            height=height, width=width, align="left", font="Times-Italic",
            size=15)

        # Conference location
        if self._conf.getLocation():
            height -= 0.7*cm
            self._drawWrappedString(
                c,
                escape(self._conf.getLocation().getName()),
                height=height, width=width, size=15, align="left",
                font="Times-Italic")

        # e-Ticket
        c.setFont('Times-Bold', 30)
        height -= 2*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0, height, _("e-ticket"))

        # QRCode (Version 6 with error correction L can contain up to 106 bytes)
        height -= 6*cm
        qr = QRCode(
            version=6,
            error_correction=constants.ERROR_CORRECT_M,
            box_size=4,
            border=1
        )
        config = Config.getInstance()
        baseURL = config.getBaseSecureURL() if config.getBaseSecureURL() else config.getBaseURL()
        qr_data = {"registrant_id": self._registrant.getId(),
                   "secret": self._registrant.getCheckInUUID(),
                   "event_id": self._conf.getId(),
                   "server_url": baseURL
                  }
        json_qr_data = json.dumps(qr_data)
        qr.add_data(json_qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image()

        c.drawImage(ImageReader(qr_img._img), width, height, height=4*cm,
                    width=4*cm)

        # QRCode and registrant info separating line
        width += 4.5*cm
        c.setStrokeColorRGB(0, 0, 0)
        c.line(width, height, width, height + 4*cm)

        # Registrant info
        width += 0.5*cm
        height += 3*cm
        self._drawWrappedString(c, escape(self._registrant.getFullName()),
                                height=height, width=width, size=15,
                                align="left", font='Times-Roman')
        if self._registrant.getInstitution():
            height -= 0.5*cm
            self._drawWrappedString(c,
                                    escape(self._registrant.getInstitution()),
                                    height=height, width=width, size=15,
                                    align="left", font='Times-Roman')
        if self._registrant.getAddress():
            height -= 0.5*cm
            self._drawWrappedString(c, escape(self._registrant.getAddress()),
                                    height=height, width=width, size=15,
                                    align="left", font='Times-Roman')
        if self._registrant.getCity():
            height -= 0.5*cm
            self._drawWrappedString(c, escape(self._registrant.getCity()),
                                    height=height, width=width, size=15,
                                    align="left", font='Times-Roman')
        if self._registrant.getCountry():
            height -= 0.5*cm
            self._drawWrappedString(c, escape(self._registrant.getCountry()),
                                    height=height, width=width, size=15,
                                    align="left", font='Times-Roman')
        c.restoreState()
