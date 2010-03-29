# -*- coding: utf-8 -*-
##
## $Id: tracks.py,v 1.66 2009/06/17 12:37:18 pferreir Exp $
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from xml.sax.saxutils import quoteattr, escape
from urllib import quote
from datetime import datetime,timedelta
from MaKaC.webinterface.pages.conferences import WPConferenceBase, WPConferenceModifBase
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
from MaKaC.webinterface.pages.conferences import WContribParticipantList
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface import wcomponents
from MaKaC import review
from MaKaC.common import Config
from MaKaC.common import filters
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.i18n import _

class WPTrackBase(WPConferenceBase):

    def __init__( self, rh, track, subTrack=None):
        WPConferenceBase.__init__( self, rh, track.getConference() )
        self._track = track
        self._subTrack = subTrack


class WPTrackDisplayBase( WPTrackBase ):
    pass


class WPTrackDefaultDisplayBase( WPTrackDisplayBase, WPConferenceDefaultDisplayBase ):

    def __init__( self, rh, track ):
        WPTrackDisplayBase.__init__( self, rh, track )

    def _applyDecoration( self, body ):
        return WPConferenceDefaultDisplayBase._applyDecoration( self, body )

    def _display(self,params):
        return WPConferenceDefaultDisplayBase._display(self,params)


class WPTrackDisplay( WPTrackDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = wcomponents.WTrackDisplay( self._getAW(), self._track )
        pars = { \
"trackModifURL": urlHandlers.UHTrackModification.getURL( self._track ), \
"materialURLGen": urlHandlers.UHMaterialDisplay.getURL, \
"contribURLGen": urlHandlers.UHContributionDisplay.getURL }
        return wc.getHTML( pars )


class WPTrackModifBase( WPConferenceModifBase ):

    def __init__( self, rh, track, subTrack=None):
        WPConferenceModifBase.__init__( self, rh, track.getConference() )
        self._track = track
        self._subTrack = subTrack

    def _getNavigationDrawer(self):
        if self._subTrack:
            target = self._subTrack
        else:
            target = self._track
        pars = {"target": target, "isModif": True}
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHTrackModification.getURL( self._track ) )
        self._tabSubTrack = None
        self._tabCoordination= self._tabCtrl.newTab( "cc", \
                 _("Coordination control"), \
                urlHandlers.UHTrackModifCoordination.getURL( self._track ) )
        self._tabAbstracts = self._tabCtrl.newTab( "abstracts", _("Abstracts"), \
                urlHandlers.UHTrackModifAbstracts.getURL( self._track ) )
        if self._conf.hasEnabledSection("cfa"):
            self._tabAbstracts.enable()
            self._tabCoordination.enable()
        else:
            self._tabAbstracts.disable()
            self._tabCoordination.disable()
        self._tabContribs=self._tabCtrl.newTab( "contribs", _("Contributions"), \
                urlHandlers.UHTrackModContribList.getURL(self._track))
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _setActiveSideMenuItem( self ):
        self._programMenuItem.setActive()

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WTrackBannerModif(self._track, isManager=self._tabMain.isEnabled()).getHTML()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner+html

    def _getTabContent( self, params ):
        return  _("nothing")


class WTrackModifMain(wcomponents.WTemplated):

    def __init__(self,track):
        self._track = track

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["title"]=self.htmlText(self._track.getTitle())
        vars["description"]=self.htmlText(self._track.getDescription())
        vars["code"]=self.htmlText(self._track.getCode())
        vars["dataModificationURL"]=quoteattr(str(urlHandlers.UHTrackDataModif.getURL(self._track)))
        return vars


class WPTrackModification( WPTrackModifBase ):

    def _getTabContent( self, params ):
        comp=WTrackModifMain(self._track)
        return comp.getHTML()


class WTrackDataModification(wcomponents.WTemplated):

    def __init__(self,track):
        self._track=track
        self._conf=track.getConference()

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["code"]=quoteattr(str(self._track.getCode()))
        vars["title"]=quoteattr(str(self._track.getTitle()))
        vars["description"]=self.htmlText(self._track.getDescription())
        vars["postURL"]=quoteattr(str(urlHandlers.UHTrackPerformDataModification.getURL(self._track)))
        return vars


class WPTrackDataModification( WPTrackModification ):

    def _getTabContent( self, params ):
        p=WTrackDataModification(self._track)
        return p.getHTML()


class _AbstractStatusTrackView:
    _label = ""
    _color = ""
    _id = ""
    _icon = ""

    def __init__( self, track, abstract ):
        self._track = track
        self._abstract = abstract

    def getLabel( cls ):
        return _(cls._label)
    #ne pas oublier d'appeler la fonction de traduction
    getLabel=classmethod(getLabel)

    def getComment( self ):
        return ""

    def getResponsible( self ):
        return None

    def getDate( self ):
        return None

    def getColor( cls ):
        return cls._color
    getColor = classmethod( getColor )

    def getId( cls ):
        return cls._id
    getId = classmethod( getId )

    def getIconURL( cls ):
        return Config.getInstance().getSystemIconURL( cls._icon )
    getIconURL = classmethod( getIconURL )


class _ASTrackViewSubmitted( _AbstractStatusTrackView ):
    _color = "white"
    _id = "submitted"
    _icon = "ats_submitted"
    #don't modify it _("submitted")
    _label = "submitted"

class _ASTrackViewAccepted( _AbstractStatusTrackView ):
    _color = "white"
    _id = "accepted"
    _icon = "ats_accepted"
    #don't modify it _("accepted")
    _label = "accepted"

    def getComment( self ):
        return  self._abstract.getCurrentStatus().getComments()

    def getResponsible( self ):
        return self._abstract.getCurrentStatus().getResponsible()

    def getDate( self ):
        return self._abstract.getCurrentStatus().getDate()

    def getContribType(self):
        return self._abstract.getCurrentStatus().getType()


class _ASTrackViewAcceptedForOther( _AbstractStatusTrackView ):
    _color = "white"
    _id = "accepted_other"
    _icon = "ats_accepted_other"
    #don't modify it _("accepted for other track")
    _label = "accepted for other track"

    def getComment( self ):
        return  self._abstract.getCurrentStatus().getComments()

    def getResponsible( self ):
        return self._abstract.getCurrentStatus().getResponsible()

    def getDate( self ):
        return self._abstract.getCurrentStatus().getDate()

    def getTrack( self ):
        return self._abstract.getCurrentStatus().getTrack()


class _ASTrackViewRejected( _AbstractStatusTrackView ):
    _color = "white"
    _id = "rejected"
    _icon = "ats_rejected"
    #don't modify it _("rejected")
    _label = "rejected"

    def getComment( self ):
        return  self._abstract.getCurrentStatus().getComments()

    def getResponsible( self ):
        return self._abstract.getCurrentStatus().getResponsible()

    def getDate( self ):
        return self._abstract.getCurrentStatus().getDate()


class _ASTrackViewPA( _AbstractStatusTrackView ):
    _color = "white"
    _id = "pa"
    _icon = "ats_prop_accept"
    #next comment is for translation extraction
    # _("proposed to be accepted")
    _label = "proposed to be accepted"

    def getComment( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getComment()

    def getResponsible( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getResponsible()

    def getDate( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getDate()

    def getContribType( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getContribType()

    def getConflicts( self ):
        #Event if the abstract is not in "in conflict" status we want to
        #   show up current conflicts
        acc = self._abstract.getTrackAcceptanceList()
        #If there is only 1 track judgement accepting the abstract and it's
        #   ours, then no conflict is reported
        if len( acc ) == 1 and acc[0].getTrack() == self._track:
            return []
        return acc


class _ASTrackViewPR( _AbstractStatusTrackView ):
    _color = "white"
    _id = "pr"
    _icon = "ats_prop_reject"
    #don't modify it _("rejected")
    _label = "proposed to be rejected"

    def getComment( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getComment()

    def getResponsible( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getResponsible()

    def getDate( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getDate()


class _ASTrackViewPFOT( _AbstractStatusTrackView ):
    _color = "white"
    _id = "pfot"
    _icon = "ats_prop_other_track"
    #don't modify it _("rejected")
    _label = "proposed for other tracks"

    def getComment( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getComment()

    def getResponsible( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getResponsible()

    def getDate( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getDate()

    def getProposedTrackList( self ):
        jud = self._abstract.getTrackJudgement( self._track )
        return jud.getProposedTrackList()


class _ASTrackViewWithdrawn( _AbstractStatusTrackView ):
    _color = "white"
    _id = "withdrawn"
    _icon = "ats_withdrawn"
    #don't modify it _("withdrawn")
    _label = "withdrawn"

    def getComment( self ):
        return  self._abstract.getCurrentStatus().getComments()

    def getDate( self ):
        return self._abstract.getCurrentStatus().getDate()


class _ASTrackViewDuplicated( _AbstractStatusTrackView ):
    _color = "white"
    _id = "duplicated"
    _icon = "ats_withdrawn"
    #don't modify it _("duplicated")
    _label = "duplicated"

    def getComment( self ):
        return  self._abstract.getCurrentStatus().getComments()

    def getResponsible( self ):
        return self._abstract.getCurrentStatus().getResponsible()

    def getDate( self ):
        return self._abstract.getCurrentStatus().getDate()

    def getOriginal(self):
        return self._abstract.getCurrentStatus().getOriginal()


class _ASTrackViewMerged(_AbstractStatusTrackView):
    _color = "white"
    _id = "merged"
    _icon = "ats_withdrawn"
    #don't modify it _("merged")
    _label = "merged"

    def getComment( self ):
        return  self._abstract.getCurrentStatus().getComments()

    def getResponsible( self ):
        return self._abstract.getCurrentStatus().getResponsible()

    def getDate( self ):
        return self._abstract.getCurrentStatus().getDate()

    def getTarget(self):
        return self._abstract.getCurrentStatus().getTargetAbstract()

class AbstractStatusTrackViewFactory:

    def __init__(self):
        self._status = {
            _ASTrackViewSubmitted.getId(): _ASTrackViewSubmitted, \
            _ASTrackViewAccepted.getId(): _ASTrackViewAccepted, \
            _ASTrackViewAcceptedForOther.getId(): _ASTrackViewAcceptedForOther, \
            _ASTrackViewRejected.getId(): _ASTrackViewRejected, \
            _ASTrackViewPA.getId(): _ASTrackViewPA, \
            _ASTrackViewPR.getId(): _ASTrackViewPR, \
            _ASTrackViewPFOT.getId(): _ASTrackViewPFOT, \
            _ASTrackViewWithdrawn.getId(): _ASTrackViewWithdrawn,\
            _ASTrackViewDuplicated.getId(): _ASTrackViewDuplicated, \
            _ASTrackViewMerged.getId(): _ASTrackViewMerged }

    def getStatus( track, abstract ):
        d = { \
        review.AbstractStatusSubmitted: _ASTrackViewSubmitted, \
        review.AbstractStatusRejected: _ASTrackViewRejected, \
        review.AbstractStatusWithdrawn: _ASTrackViewWithdrawn, \
        review.AbstractStatusDuplicated: _ASTrackViewDuplicated, \
        review.AbstractStatusMerged: _ASTrackViewMerged \
            }
        status = abstract.getCurrentStatus()
        if d.has_key( status.__class__ ):
            return d[ status.__class__ ](track, abstract)
        #   return d[ status.__class__ ](track, abstract)
        #For the accepted status, we need to know if it has been accepted for
        #   the current track
        if status.__class__ == review.AbstractStatusAccepted:
            if status.getTrack() != track:
                return _ASTrackViewAcceptedForOther( track, abstract )
            return _ASTrackViewAccepted( track, abstract )
        #If it is not in one of the "common" status we must see if a judgement
        #   for the current track has already been done
        jud = abstract.getTrackJudgement( track )
        if jud:
            if jud.__class__ == review.AbstractAcceptance:
                return _ASTrackViewPA( track, abstract )
            elif jud.__class__ == review.AbstractRejection:
                return _ASTrackViewPR( track, abstract )
            elif jud.__class__ == review.AbstractReallocation:
                return _ASTrackViewPFOT( track, abstract )
        #If no judgement exists for the current track the abstract is in
        #   SUBMITTED status for the track
        return _ASTrackViewSubmitted( track, abstract )
    getStatus = staticmethod( getStatus )

    def getStatusList( self ):
        return self._status.values()

    def getStatusById( self, id ):
        return self._status[id]


class WTrackModifAbstracts( wcomponents.WTemplated ):

    def __init__( self, track, filterCrit, sortingCrit ):
        self._track = track

        self._conf = self._track.getConference()
        self._filterCrit = filterCrit
        self._sortingCrit = sortingCrit

    def _getAbstractHTML( self, abstract ):
        aStatus = AbstractStatusTrackViewFactory().getStatus( self._track, abstract )
        url = urlHandlers.UHTrackAbstractModif.getURL( self._track, abstract )
        label = aStatus.getLabel()
        icon = """<img src=%s border="0" alt="">"""%quoteattr( str( aStatus.getIconURL() ) )
        accType=""
        if isinstance(aStatus,_ASTrackViewPA):
            label="""%s"""%(label)
            if aStatus.getContribType() is not None and aStatus.getContribType()!="":
                accType=aStatus.getContribType().getName()
            if aStatus.getConflicts():
                label = _("""%s<br><font color="red">[ _("conflicts") ]</font>""")%label
        elif isinstance(aStatus,_ASTrackViewAccepted):
            if aStatus.getContribType() is not None and aStatus.getContribType()!="":
                accType=aStatus.getContribType().getName()
                label="""%s"""%(label)
        contribType=abstract.getContribType()
        contribTypeName = _("""--_("not specified")--""")
        if contribType is not None:
            contribTypeName=contribType.getName()
        comments = ""
        if abstract.getComments():
            comments = _(""" <img src=%s alt="_("The submitter filled some comments")">""")%(quoteattr(Config.getInstance().getSystemIconURL("comments")))
        html = """
        <tr>
            <td nowrap class="abstractLeftDataCell">%s%s</td>
            <td width="100%%" align="left" valign="top" class="abstractDataCell">
                <input type="checkbox" name="abstracts" value=%s%s> <a href=%s>%s</a></td>
            <td valign="top" class="abstractDataCell">%s</td>
            <td nowrap valign="top" class="abstractDataCell">%s %s</td>
            <td valign="top" class="abstractDataCell">%s</td>
            <td nowrap valign="top" class="abstractDataCell">%s</td>
        </tr>
                """%(self.htmlText(abstract.getId()),comments,\
                    quoteattr(str(abstract.getId())),self._checked, \
                    quoteattr(str(url)),self.htmlText(abstract.getTitle()),\
                    self.htmlText(contribTypeName),icon, \
                    label,self.htmlText(accType),\
                    abstract.getSubmissionDate().strftime("%d %B %Y"))
        return html

    def _getURL( self ):
        #builds the URL to the track management abstract list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHTrackModifAbstracts.getURL( self._track )
        if self._filterCrit.getField( "type" ):
            l=[]
            for t in self._filterCrit.getField( "type" ).getValues():
                if t:
                    l.append(t.getId())
            url.addParam( "selTypes", l )
            if self._filterCrit.getField( "type" ).getShowNoValue():
                url.addParam( "typeShowNoValue", "1" )
        if self._filterCrit.getField( "status" ):
            url.addParam( "selStatus", self._filterCrit.getField( "status" ).getValues() )
        if self._filterCrit.getField( "acc_type" ):
            l=[]
            for t in self._filterCrit.getField( "acc_type" ).getValues():
                if t:
                    l.append(t.getId())
            url.addParam("selAccTypes",l)
            if self._filterCrit.getField( "acc_type" ).getShowNoValue():
                url.addParam( "accTypeShowNoValue", "1" )
        if self._filterCrit.getField( "multiple_tracks" ):
            url.addParam( "selMultipleTracks", "1" )
        if self._filterCrit.getField( "comment" ):
            url.addParam( "selOnlyComment", "1" )
        if self._sortingCrit.getField():
            url.addParam( "sortBy", self._sortingCrit.getField().getId() )
        url.addParam("OK", "1")
        url.setSegment("abstracts")
        return url

    def _getTypeFilterItemList( self ):
        checked = ""
        if self._filterCrit.getField("type").getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="typeShowNoValue"%s> --_("not specified")--""")%checked]
        #for type in self._conf.getAbstractMgr().getContribTypeList():
        for type in self._conf.getContribTypeList():
            checked = ""
            if type in self._filterCrit.getField("type").getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="selTypes" value=%s%s> %s"""%(quoteattr(type.getId()), checked, self.htmlText(type.getName())) )
        return l

    def _getAccTypeFilterItemList(self):
        checked=""
        if self._filterCrit.getField("acc_type").getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="accTypeShowNoValue"%s> --_("not specified")--""")%checked]
        for type in self._conf.getContribTypeList():
            checked = ""
            if type in self._filterCrit.getField("acc_type").getValues():
                checked=" checked"
            l.append("""<input type="checkbox" name="selAccTypes" value=%s%s> %s"""%(quoteattr(type.getId()),checked,self.htmlText(type.getName())))
        return l

    def _getStatusFilterItemList( self ):
        l = []
        for statusKlass in AbstractStatusTrackViewFactory().getStatusList():
            checked = ""
            statusId = statusKlass.getId()
            statusCaption = statusKlass.getLabel()
            if statusId in self._filterCrit.getField("status").getValues():
                checked = " checked"
            iconHTML = """<img src=%s border="0" alt="">"""%quoteattr( str( statusKlass.getIconURL() ) )
            l.append( """<input type="checkbox" name="selStatus" value=%s%s> %s %s"""%(quoteattr(statusId), checked, iconHTML, self.htmlText( statusCaption )) )
        return l

    def _getOthersFilterItemList( self ):
        checkedMulTracks, checkedOnlyComment = "", ""
        if self._filterCrit.getField("multiple_tracks"):
            checkedMulTracks = " checked"
        if self._filterCrit.getField("comment"):
            checkedOnlyComment = " checked"
        l = [ _("""<input type="checkbox" name="selMultipleTracks"%s> _("only multiple tracks")""")%checkedMulTracks, \
                 _("""<input type="checkbox" name="selOnlyComment"%s> _("only with comments")""")%checkedOnlyComment]
        return l

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["types"] = "<br>".join( self._getTypeFilterItemList() )
        vars["status"] = "<br>".join( self._getStatusFilterItemList() )
        vars["others"] = "<br>".join( self._getOthersFilterItemList() )
        vars["accTypes"] = "<br>".join( self._getAccTypeFilterItemList() )
        f = filters.SimpleFilter(self._filterCrit,self._sortingCrit)
        al = []
        abstractsToPrint = []
        self._checked = ""
        if vars["selectAll"]:
            self._checked = " checked"
        abstractList = f.apply( self._track.getAbstractList() )
        for abstract in abstractList:
            al.append( self._getAbstractHTML( abstract ) )
            abstractsToPrint.append("""<input type="hidden" name="abstracts" value="%s">"""%abstract.getId())
        vars["number"] = str(len(abstractList))
        vars["abstracts"] = "".join( al )
        vars["abstractsToPrint"] = "\n".join(abstractsToPrint)

        sortingField = self._sortingCrit.getField()
        vars["currentSorting"] = ""
        url = self._getURL()
        url.addParam("sortBy", "type")
        vars["typeSortingURL"] = quoteattr( str( url ) )
        vars["typeImg"] = ""
        if sortingField and sortingField.getId() == "type":
            vars["typeImg"] = """<img src=%s alt="">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="type">"""
        url = self._getURL()
        url.addParam("sortBy", "status")
        vars["statusSortingURL"] = quoteattr( str( url ) )
        vars["statusImg"] = ""
        if sortingField and sortingField.getId() == "status":
            vars["statusImg"] = """<img src=%s alt="">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="status">"""
        url = self._getURL()
        url.addParam("sortBy", "number")
        vars["numberSortingURL"] = quoteattr( str( url ) )
        vars["numberImg"] = ""
        if sortingField and sortingField.getId() == "number":
            vars["numberImg"] = """<img src=%s alt="">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="number">"""

        url = self._getURL()
        url.addParam("sortBy", "date")
        vars["dateSortingURL"] = quoteattr( str( url ) )
        vars["dateImg"] = ""
        if sortingField and sortingField.getId() == "date":
            vars["dateImg"] = """<img src=%s alt="">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="date">"""
        url = urlHandlers.UHTrackModifAbstracts.getURL( self._track )
        url.setSegment( "abstracts" )
        vars["filterPostURL"]=quoteattr(str(url))
        vars["accessAbstract"] = quoteattr(str(urlHandlers.UHTrackAbstractDirectAccess.getURL(self._track)))
        vars["allAbstractsURL"] = quoteattr( str( urlHandlers.UHConfAbstractManagment.getURL( self._conf ) ) )
        l = []
        for tpl in self._conf.getAbstractMgr().getNotificationTplList():
            l.append("""<option value="%s">%s</option>"""%(tpl.getId(), tpl.getName()))
        vars["notifTpls"] = "\n".join(l)
        vars["participantListURL"]=quoteattr(str(urlHandlers.UHAbstractsTrackManagerParticipantList.getURL(self._track)))
        vars["abstractsPDFURL"]=quoteattr(str(urlHandlers.UHAbstractsTrackManagerDisplayPDF.getURL(self._track)))
        vars["actionURL"]=quoteattr(str(urlHandlers.UHAbstractsTrackManagerAction.getURL(self._track)))
        vars["selectURL"]=quoteattr(str(urlHandlers.UHTrackModifAbstracts.getURL(self._track)))
        return vars


class WPTrackModifAbstracts( WPTrackModifBase ):

    def __init__(self, rh, track, msg):
        self._msg = msg
        WPTrackModifBase.__init__(self, rh, track)

    def _setActiveTab( self ):
        conf = self._track.getConference()
        if not conf.canModify( self._getAW() ):
            self._tabMain.disable()
            self._tabCoordination.disable()
        self._tabAbstracts.setActive()

    def _getTabContent( self, params ):

        wc = WTrackModifAbstracts( self._track, \
                                    params["filterCrit"], \
                                    params["sortingCrit"]  )
        pars = { "selectAll": params.get("selectAll", None), \
                "directAbstractMsg": escape(self._msg) }
        return wc.getHTML(pars)


#class WTrackModifFrame(wcomponents.WTemplated):
#
#    def __init__( self, track, aw):
#        self._track = track
#        self._aw = aw
#
#    def getHTML( self, body, **params):
#        params["body"] = body
#        return wcomponents.WTemplated.getHTML( self, params )
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["target"] = self._track
#        return vars
#
#    def getOwnerComponent( self ):
#        owner = self._track.getOwner()
#        wc = wcomponents.WConferenceModifFrame(owner, self._aw)
#        return wc
#
#    def getIntermediateVTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return 7 + wc.getIntermediateVTabPixels()
#
#    def getTitleTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return wc.getTitleTabPixels() - 7
#
#    def getCloseHeaderTags( self ):
#        wc = self.getOwnerComponent()
#        return "</table></td></tr>" + wc.getCloseHeaderTags()


#class WTrackModifHeader(wcomponents.WTemplated):
#
#    def __init__( self, track, aw ):
#        self._track = track
#        self._aw = aw
#
#    def getHTML( self, params ):
#        conf = self._track.getConference()
#        confHTML = wcomponents.WConfModifHeader( conf, self._aw ).getHTML( params )
#        return "%s%s"%(confHTML, wcomponents.WTemplated.getHTML( self, params ) )
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        URLGen = vars.get( "trackModifURLGen", urlHandlers.UHTrackModification.getURL )
#        vars["trackModificationURL"] = URLGen(self._track)
#        conf = self._track.getConference()
#        vars["trackDisplayURL"] = urlHandlers.UHConferenceProgram.getURL( conf )
#        vars["imgGestionGrey"] = Config.getInstance().getSystemIconURL( "gestionGrey" )
#        vars["title"] = self._track.getTitle()
#        vars["titleTabPixels"] = WTrackModifFrame(self._track, self._aw).getTitleTabPixels()
#        return vars


class WPTrackAbstractModifBase( WPConferenceModifBase ):

    def __init__( self, rh, track, abstract ):
        self._abstract = abstract
        self._track = track
        WPConferenceModifBase.__init__( self, rh, self._track.getConference() )

    def _getNavigationDrawer(self):
        pars = {"target": self._abstract, "isModif": True, "track": self._track}
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WTrackBannerModif(self._track, self._abstract, isManager=self._abstract.getConference().canModify( self._getAW() )).getHTML()
        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner + body

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
            urlHandlers.UHTrackAbstractModif.getURL(self._track,self._abstract))
        nComments=""
        if len(self._abstract.getIntCommentList()) > 0:
            nComments = " (%s)"%len(self._abstract.getIntCommentList())
        self._tabComments=self._tabCtrl.newTab( "comments", _("Internal comments%s")%nComments,\
            urlHandlers.UHTrackAbstractModIntComments.getURL(self._track,self._abstract))
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return _("nothing")

    def _setActiveSideMenuItem(self):
        self._programMenuItem.setActive()


class WTrackAbstractModification( wcomponents.WTemplated ):

    def __init__( self, track, abstract ):
        self._track = track
        self._abstract = abstract

    def _getAuthorHTML( self, auth ):
        tmp = "%s (%s)"%(auth.getFullName(), auth.getAffiliation())
        tmp = self.htmlText( tmp )
        if auth.getEmail() != "":
            mailtoSubject =  _("""[%s]  _("Abstract") %s: %s""")%( self._track.getConference().getTitle(), self._abstract.getId(), self._abstract.getTitle() )
            mailtoURL = "mailto:%s?subject=%s"%( auth.getEmail(), quote( mailtoSubject ) )
            href = quoteattr( mailtoURL )
            tmp = """<a href=%s>%s</a>"""%(href, tmp)
        return tmp

    def _getStatusDetailsHTML( self, status ):
        details = ""
        if status.getResponsible():
            details= _("""<font size="-1">_("by") <i>%s</i></font>""")%( self._getAuthorHTML( status.getResponsible() ) )
        if status.getDate():
            details = _("""%s <font size="-1">_("on") %s</font> """)%( details, status.getDate().strftime( "%d %B %Y %H:%M" ) )
        res = "%s"%self.htmlText( status.getLabel().upper() )
        if isinstance(status, _ASTrackViewPFOT):
            l = []
            for track in status.getProposedTrackList():
                l.append( self.htmlText( track.getTitle() ) )
            res = """%s: <br><font size="-1">%s</font>"""%(res, ", ".join(l))
        elif isinstance(status, _ASTrackViewPA):
            ct=""
            if status.getContribType() is not None:
                ct=" (%s)"%self.htmlText(status.getContribType().getName())
            res = "%s%s"%(self.htmlText( status.getLabel().upper()),ct)
        elif isinstance(status, _ASTrackViewDuplicated):
            orig=status.getOriginal()
            url=urlHandlers.UHAbstractManagment.getURL(orig)
            originalHTML="""<a href=%s target="_blank">%s-%s</a>"""%(\
                            quoteattr(str(url)), \
                            self.htmlText(orig.getId()),\
                            self.htmlText(orig.getTitle()))
            if self._track.hasAbstract(orig):
                url=urlHandlers.UHTrackAbstractModif.getURL(self._track,orig)
                originalHTML="<a href=%s>%s-%s</a>"%( quoteattr(str(url)), \
                                self.htmlText(orig.getId()),\
                                self.htmlText(orig.getTitle()))
            res = """%s (%s)"""%(self.htmlText( status.getLabel().upper()), \
                        originalHTML)
        elif isinstance(status, _ASTrackViewMerged):
            target=status.getTarget()
            url=urlHandlers.UHAbstractManagment.getURL(target)
            originalHTML="""<a href=%s target="_blank">%s-%s</a>"""%(\
                            quoteattr(str(url)), \
                            self.htmlText(target.getId()),\
                            self.htmlText(target.getTitle()))
            if self._track.hasAbstract(target):
                url=urlHandlers.UHTrackAbstractModif.getURL(self._track,target)
                originalHTML="<a href=%s>%s-%s</a>"%( quoteattr(str(url)), \
                                self.htmlText(target.getId()),\
                                self.htmlText(target.getTitle()))
            res = """%s (%s)"""%(self.htmlText( status.getLabel().upper()), \
                        originalHTML)
        elif isinstance(status,_ASTrackViewAccepted):
            if status.getContribType() is not None and \
                                            status.getContribType()!="":
                res = "%s as %s"%(self.htmlText(status.getLabel().upper()), \
                             self.htmlText(status.getContribType().getName()))
        if details != "":
            res = """%s <br><font size="-1">%s</font>"""%( res, details )
        return res

    def _getStatusCommentsHTML( self, status ):
        comment = ""
        if status.getComment() != "":
            comment = self.htmlText( status.getComment() )
        if status.__class__ == _ASTrackViewPA:
            conflicts = status.getConflicts()
            if conflicts:
                if comment != "":
                    comment = "%s<br><br>"%comment
                l = []
                for jud in conflicts:
                    if jud.getTrack() != self._track:
                        l.append( "%s ( %s )"%( jud.getTrack().getTitle(), \
                                self._getAuthorHTML( jud.getResponsible() ) ) )
                comment = _("""%s<font color="red">_("In conflict with"): <br> %s</font>""")%(comment, "<br>".join(l) )
        rl = self._abstract.getReallocationTargetedList( self._track )
        if rl:
            comment = _("""%s<br><br><font color="green">_("Proposed by") <i>%s</i>(%s): <br>%s</font>""")%(comment, \
                    self.htmlText( rl[0].getTrack().getTitle() ), \
                    self._getAuthorHTML( rl[0].getResponsible() ), \
                    self.htmlText( rl[0].getComment() ) )
        return comment

    def _getContribHTML(self):
        res = ""
        contrib = self._abstract.getContribution()
        if contrib is not None:
            url=urlHandlers.UHContributionModification.getURL(contrib)
            title=self.htmlText(contrib.getTitle())
            id=self.htmlText(contrib.getId())
            res = """<a href=%s>%s - %s</a>"""%(quoteattr(str(url)),id,title)
        return res

    def _getAdditionalFieldsHTML(self):
        html=""
        afm = self._abstract.getConference().getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getActiveFields():
            id = f.getId()
            caption = f.getName()
            html+="""
                    <tr>
                        <td class="dataCaptionTD"><span class="dataCaptionFormat">%s</span></td>
                        <td bgcolor="white"><pre>%s</pre></td>
                    </tr>
                """%(self.htmlText(caption), self.htmlText(self._abstract.getField(id)) )
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.htmlText( self._abstract.getTitle() )
        vars["abstractPDF"] = urlHandlers.UHAbstractTrackManagerDisplayPDF.getURL( self._track, self._abstract )
        vars["printIconURL"] = Config.getInstance().getSystemIconURL( "pdf" )
        vars["additionalFields"] = self._getAdditionalFieldsHTML()
        primary = []
        for author in self._abstract.getPrimaryAuthorList():
            primary.append(self._getAuthorHTML(author))
        vars["primary_authors"] = "<br>".join( primary )
        secondary = []
        for author in self._abstract.getCoAuthorList():
            secondary.append(self._getAuthorHTML(author))
        vars["co_authors"] = "<br>".join( secondary )
        speakers = []
        for author in self._abstract.getSpeakerList():
            speakers.append(self._getAuthorHTML(author))
        vars["speakers"] = "<br>".join( speakers )
        vars["type"] = _("""--_("not specified")--""")
        if self._abstract.getContribType() is not None:
            vars["type"] = self.htmlText( self._abstract.getContribType().getName() )
        tracks = []
        for track in self._abstract.getTrackListSorted():
            tracks.append( """%s"""%track.getTitle() )
        vars["tracks"] = "<br>".join( tracks )
        vars["submitter"] = self._getAuthorHTML( self._abstract.getSubmitter() )
        vars["submissionDate"] = self._abstract.getSubmissionDate().strftime( "%d %B %Y %H:%M" )
        vars["modificationDate"] = self._abstract.getModificationDate().strftime( "%d %B %Y %H:%M" )

        aStatus = AbstractStatusTrackViewFactory().getStatus( self._track, self._abstract )
        vars["statusDetails"] = self._getStatusDetailsHTML( aStatus )
        vars["statusComment"] = self._getStatusCommentsHTML( aStatus )
        vars["statusColor"] = aStatus.getColor()
        vars["modifyStatusURL"],vars["modifyStatusBtn"]=quoteattr(""),""
        vars["PA_defaults"]=""

        vars["proposeToAcceptButton"] = _("""<input type="submit" class="btn" value="_("propose to be accepted")" style="width:205px">""")
        vars["proposeToRejectButton"] = _("""<input type="submit" class="btn" value="_("propose to be rejected")" style="width:205px">""")
        vars["proposeForOtherTracksButton"] = _("""<input type="submit" class="btn" value="_("propose for other tracks")" style="width:205px">""")

        if isinstance(aStatus,_ASTrackViewPA):
            vars["PA_defaults"]="""
                <input type="hidden" name="comment" value=%s>
                <input type="hidden" name="contribType" value=%s>
                                """%(quoteattr(str(aStatus.getComment())),\
                                    quoteattr(str(aStatus.getContribType())))
            vars["modifyStatusBtn"]= _("""<input type="submit" class="btn" value="_("modify proposition")">""")
            vars["modifyStatusURL"]=quoteattr(str(urlHandlers.UHTrackAbstractPropToAcc.getURL(self._track,self._abstract)))
        vars["proposeToAccURL"]=quoteattr(str(urlHandlers.UHTrackAbstractPropToAcc.getURL(self._track,self._abstract)))
        vars["proposeToRejURL"]=quoteattr(str(urlHandlers.UHTrackAbstractPropToRej.getURL(self._track,self._abstract)))
        vars["proposeForOtherTracksURL"] = quoteattr( str( urlHandlers.UHTrackAbstractPropForOtherTrack.getURL( self._track, self._abstract) ) )
        vars["comments"] = self._abstract.getComments()
        vars["abstractId"] = self._abstract.getId()
        vars["duplicatedURL"]=quoteattr(str(urlHandlers.UHTrackAbstractModMarkAsDup.getURL(self._track,self._abstract)))
        vars["duplicatedButton"]=""
        if aStatus.__class__ in [_ASTrackViewPA,_ASTrackViewPR,_ASTrackViewSubmitted,_ASTrackViewPFOT]:
            vars["duplicatedButton"]= _("""<input type="submit" class="btn" value="_("mark as duplicated")" style="width:205px">""")
        elif aStatus.__class__ == _ASTrackViewDuplicated:
            vars["duplicatedButton"]= _("""<input type="submit" class="btn" value="_("unmark as duplicated") style="width:205px">""")
            vars["duplicatedURL"]=quoteattr(str(urlHandlers.UHTrackAbstractModUnMarkAsDup.getURL(self._track,self._abstract)))
        vars["contribution"]=self._getContribHTML()
        return vars


class WPTrackAbstractModif( WPTrackAbstractModifBase ):

    def _getTabContent( self, params ):
        wc = WTrackAbstractModification( self._track, self._abstract )
        return wc.getHTML()


class WTrackAbstractPropToAcc( wcomponents.WTemplated ):

    def __init__( self, track, abstract ):
        self._abstract = abstract
        self._track = track

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractTitle"] = self._abstract.getTitle()
        vars["trackTitle"] = self._track.getTitle()
        vars["postURL"] = urlHandlers.UHTrackAbstractPropToAcc.getURL( self._track, self._abstract )
        l = []
        conf = self._abstract.getConference()
        for ctype in conf.getContribTypeList():
            selected = ""
            if vars.has_key("contribType"):
                if ctype==vars["contribType"]:
                    selected = " selected"
            elif self._abstract.getContribType()==ctype:
                selected = " selected"
            l.append( """<option value="%s"%s>%s</option>"""%(ctype.getId(), selected, ctype.getName() ) )
        vars["contribTypes"] = ""
        if len(l) > 0:
            vars["contribTypes"] =  _("""
                                    <tr>
			              <td nowrap class="titleCellTD"><span class="titleCellFormat">
                                         _("Proposed contribution type"):
			              </td>
			              <td>&nbsp;
				         <select name="contribType">%s</select>
			              </td>
		                    </tr>
                                    """)%("".join(l))
        return vars


class WPTrackAbstractPropToAcc( WPTrackAbstractModifBase ):

    def _getTabContent( self, params ):
        wc=WTrackAbstractPropToAcc(self._track,self._abstract)
        p={"comment":params.get("comment",""),\
            "contribType":params.get("contribType",self._abstract.getContribType())}
        return wc.getHTML(p)


class WTrackAbstractPropToRej( wcomponents.WTemplated ):

    def __init__( self, track, abstract ):
        self._abstract = abstract
        self._track = track

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractTitle"] = self._abstract.getTitle()
        vars["trackTitle"] = self._track.getTitle()
        vars["postURL"] = urlHandlers.UHTrackAbstractPropToRej.getURL( self._track, self._abstract )
        return vars


class WPTrackAbstractPropToRej( WPTrackAbstractModifBase ):

    def _getTabContent( self, params ):
        wc = WTrackAbstractPropToRej( self._track, self._abstract )
        return wc.getHTML()


class WTrackAbstractPropForOtherTrack(wcomponents.WTemplated):

    def __init__( self, track, abstract ):
        self._abstract = abstract
        self._track = track

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["postURL"] = urlHandlers.UHTrackAbstractPropForOtherTrack.getURL( self._track, self._abstract )
        vars["abstractTitle"] = self._abstract.getTitle()
        vars["trackTitle"] = self._track.getTitle()
        l = []
        conf = self._abstract.getConference()
        for track in conf.getTrackList():
            checked, disabled = "", ""
            if self._abstract.hasTrack( track ):
                checked, disabled = " checked", " disabled"
            l.append("""<input type="checkbox" name="selTracks" value="%s"%s%s> %s"""%(track.getId(), checked, disabled, self.htmlText(track.getTitle())))
        vars["trackItems"] = "<br>".join( l )
        return vars

class WPAbstractPropForOtherTracks( WPTrackAbstractModifBase ):

    def _getTabContent( self, params ):
        wc = WTrackAbstractPropForOtherTrack( self._track, self._abstract )
        return wc.getHTML()


class WPModAbstractMarkAsDup(WPTrackAbstractModifBase):

    def _getTabContent( self, params ):
        wc = wcomponents.WAbstractModMarkAsDup(self._abstract)
        p={"comments":params.get("comments",""),
            "id":params.get("originalId",""),
            "errorMsg":params.get("errorMsg",""),
            "duplicateURL":urlHandlers.UHTrackAbstractModMarkAsDup.getURL(self._track,self._abstract),
            "cancelURL":urlHandlers.UHTrackAbstractModif.getURL(self._track,self._abstract)}
        return wc.getHTML(p)


class WPModAbstractUnMarkAsDup(WPTrackAbstractModifBase):

    def _getTabContent( self, params ):
        wc = wcomponents.WAbstractModUnMarkAsDup(self._abstract)
        p={ "comments":params.get("comments",""),
            "unduplicateURL":urlHandlers.UHTrackAbstractModUnMarkAsDup.getURL(self._track,self._abstract),
            "cancelURL":urlHandlers.UHTrackAbstractModif.getURL(self._track,self._abstract)}
        return wc.getHTML(p)


class WTrackModifCoordination( wcomponents.WTemplated ):

    def __init__( self, track ):
        self._track = track

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        ut = wcomponents.WPrincipalTable()
        vars["users"] = ut.getHTML( \
            self._track.getCoordinatorList(), \
            self._track,\
            urlHandlers.UHTrackSelectCoordinators.getURL(),\
            urlHandlers.UHTrackRemoveCoordinators.getURL(),
            selectable=False)
        return vars


class WPTrackModifCoordination( WPTrackModifBase ):

    def _setActiveTab( self ):
        self._tabCoordination.setActive()

    def _getTabContent( self, params ):
        wc = WTrackModifCoordination( self._track )
        return wc.getHTML()


class WPTrackModifSelectCoordinators( WPTrackModifCoordination ):

    def _getTabContent( self, params ):
        url = urlHandlers.UHTrackSelectCoordinators.getURL()
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WUserSelection( url,forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHTrackAddCoordinators.getURL()
        return wc.getHTML( params )


class WPModAbstractIntComments(WPTrackAbstractModifBase):

    def _setActiveTab( self ):
        self._tabComments.setActive()

    def _commentEditURLGen(self,comment):
        return urlHandlers.UHTrackAbstractModIntCommentEdit.getURL(self._track,comment)

    def _commentRemURLGen(self,comment):
        return urlHandlers.UHTrackAbstractModIntCommentRem.getURL(self._track,comment)
    def _getTabContent( self, params ):
        wc=wcomponents.WAbstractModIntComments(self._getAW(),self._abstract)
        p={"newCommentURL":urlHandlers.UHTrackAbstractModIntCommentNew.getURL(self._track,self._abstract),
            "commentEditURLGen":self._commentEditURLGen,
            "commentRemURLGen":self._commentRemURLGen }
        return wc.getHTML(p)


class WPModAbstractIntCommentNew(WPModAbstractIntComments):

    def _getTabContent( self, params ):
        wc=wcomponents.WAbstractModNewIntComment(self._getAW(),self._abstract)
        p={"postURL":urlHandlers.UHTrackAbstractModIntCommentNew.getURL(self._track,self._abstract)}
        return wc.getHTML(p)


class WPModAbstractIntCommentEdit(WPModAbstractIntComments):

    def __init__(self,rh,track,comment):
        self._comment=comment
        WPModAbstractIntComments.__init__(self,rh,track,comment.getAbstract())

    def _getTabContent( self, params ):
        wc=wcomponents.WAbstractModIntCommentEdit(self._comment)
        p={"postURL": urlHandlers.UHTrackAbstractModIntCommentEdit.getURL(self._track,self._comment)}
        return wc.getHTML(p)


class WTrackModContribList(wcomponents.WTemplated):

    def __init__(self,track,filterCrit, sortingCrit, order):
        self._track=track
        self._conf=self._track.getConference()
        self._filterCrit=filterCrit
        self._sortingCrit=sortingCrit
        self._order = order
        self._totaldur =timedelta(0)

    def _getURL( self ):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHTrackModContribList.getURL(self._track)
        if self._filterCrit.getField("type"):
            l=[]
            for t in self._filterCrit.getField("type").getValues():
                if t!="":
                    l.append(t)
            url.addParam("types",l)
            if self._filterCrit.getField("type").getShowNoValue():
                url.addParam("typeShowNoValue","1")

        if self._filterCrit.getField("session"):
            url.addParam("sessions",self._filterCrit.getField("session").getValues())
            if self._filterCrit.getField("session").getShowNoValue():
                url.addParam("sessionShowNoValue","1")

        if self._filterCrit.getField("status"):
            url.addParam("status",self._filterCrit.getField("status").getValues())

#        if self._filterCrit.getField("material"):
#            url.addParam("material",self._filterCrit.getField("material").getValues())

        if self._sortingCrit.getField():
            url.addParam("sortBy",self._sortingCrit.getField().getId())
            url.addParam("order","down")
        url.addParam("OK","1")
        return url

    def _getContribHTML(self,contrib):
        sdate = ""
        if contrib.isScheduled():
            sdate=contrib.getStartDate().strftime("%Y-%b-%d %H:%M" )
        title = """<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHContributionModification.getURL(contrib))), self.htmlText(contrib.getTitle()))
        strdur = ""
        if contrib.getDuration() is not None and contrib.getDuration().seconds != 0:
            strdur = (datetime(1900,1,1)+ contrib.getDuration()).strftime("%Hh%M'")
            dur = contrib.getDuration()
            self._totaldur = self._totaldur + dur
        l = []
        for spk in contrib.getSpeakerList():
            l.append( self.htmlText( spk.getFullName() ) )
        speaker = "<br>".join( l )
        session = ""
        if contrib.getSession() is not None:
            session=self.htmlText(contrib.getSession().getCode())
        cType=""
        if contrib.getType() is not None:
            cType=self.htmlText(contrib.getType().getName())
        status=contrib.getCurrentStatus()
        statusCaption=ContribStatusList().getCode(status.__class__)
        html = """
            <tr>
                <td><input type="checkbox" name="contributions" value=%s></td>
                <td valign="top" class="abstractLeftDataCell">%s</td>
                <td valign="top" nowrap class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
            </tr>
                """%(contrib.getId(), self.htmlText(contrib.getId()),\
                    sdate or "&nbsp;",strdur or "&nbsp;",cType or "&nbsp;",title or "&nbsp;",\
                        speaker or "&nbsp;",session or "&nbsp;",\
                        statusCaption or "&nbsp;")
        return html

    def _getTypeItemsHTML(self):
        checked=""
        if self._filterCrit.getField("type").getShowNoValue():
            checked=" checked"
        res=[ _("""<input type="checkbox" name="typeShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for t in self._conf.getContribTypeList():
            checked=""
            if t.getId() in self._filterCrit.getField("type").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="types" value=%s%s> %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getName())))
        return "<br>".join(res)

    def _getSessionItemsHTML(self):
        checked=""
        if self._filterCrit.getField("session").getShowNoValue():
            checked=" checked"
        res=[ _("""<input type="checkbox" name="sessionShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for s in self._conf.getSessionListSorted():
            checked=""
            if s.getId() in self._filterCrit.getField("session").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="sessions" value=%s%s> (%s) %s"""%(quoteattr(str(s.getId())),checked,self.htmlText(s.getCode()),self.htmlText(s.getTitle())))
        return "<br>".join(res)

    def _getStatusItemsHTML(self):
        res=[]
        for st in ContribStatusList().getList():
            id=ContribStatusList().getId(st)
            checked=""
            if id in self._filterCrit.getField("status").getValues():
                checked=" checked"
            code=ContribStatusList().getCode(st)
            caption=ContribStatusList().getCaption(st)
            res.append("""<input type="checkbox" name="status" value=%s%s> (%s) %s"""%(quoteattr(str(id)),checked,self.htmlText(code),self.htmlText(caption)))
        return "<br>".join(res)


    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["quickAccessURL"]=quoteattr(str(urlHandlers.UHTrackModContribQuickAccess.getURL(self._track)))
        vars["filterPostURL"]=quoteattr(str(urlHandlers.UHTrackModContribList.getURL(self._track)))
        vars["authSearch"]=""
        authField=self._filterCrit.getField("author")
        if authField is not None:
            vars["authSearch"]=quoteattr(str(authField.getValues()))
        vars["types"]=self._getTypeItemsHTML()
        vars["sessions"]=self._getSessionItemsHTML()
        vars["status"]=self._getStatusItemsHTML()
        sortingField = self._sortingCrit.getField()
        self._currentSorting=""
        if sortingField is not None:
            self._currentSorting=sortingField.getId()
        vars["currentSorting"]=""

        url=self._getURL()
        url.addParam("sortBy","number")
        vars["numberImg"]=""
        if self._currentSorting == "number":
            vars["currentSorting"] ="""<input type="hidden" name="sortBy" value="number">"""
            if self._order == "down":
                vars["numberImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["numberImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["numberSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "date")
        vars["dateImg"] = ""
        if self._currentSorting == "date":
            vars["currentSorting"]="""<input type="hidden" name="sortBy" value="date">"""
            if self._order == "down":
                vars["dateImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["dateImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["dateSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "name")
        vars["titleImg"] = ""
        if self._currentSorting == "name":
            vars["currentSorting"]="""<input type="hidden" name="sortBy" value="name">"""
            if self._order == "down":
                vars["titleImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["titleImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["titleSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "speaker")
        vars["speakerImg"]=""
        if self._currentSorting=="speaker":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="speaker">"""
            if self._order == "down":
                vars["speakerImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["speakerImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["speakerSortingURL"]=quoteattr( str( url ) )

        url = self._getURL()
        url.addParam("sortBy","session")
        vars["sessionImg"] = ""
        if self._currentSorting == "session":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="session">"""
            if self._order == "down":
                vars["sessionImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["sessionImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["sessionSortingURL"] = quoteattr( str( url ) )

        url = self._getURL()
        url.addParam("sortBy", "type")
        vars["typeImg"] = ""
        if self._currentSorting == "type":
            vars["currentSorting"]="""<input type="hidden" name="sortBy" value="type">"""
            if self._order == "down":
                vars["typeImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["typeImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["typeSortingURL"] = quoteattr( str( url ) )

        f=filters.SimpleFilter(self._filterCrit,self._sortingCrit)
        numContribs=0
        l=[]
        contribsToPrint = []
        for contrib in f.apply(self._track.getContributionList()):
            l.append(self._getContribHTML(contrib))
            numContribs+=1
            contribsToPrint.append("""<input type="hidden" name="contributions" value="%s">"""%contrib.getId())
        if self._order =="up":
            l.reverse()
        vars["contributions"] = "".join(l)
        vars["contribsToPrint"] = "".join(contribsToPrint)
        vars["numContribs"]=str(numContribs)
        vars["contributionActionURL"]=quoteattr(str(urlHandlers.UHTrackModContributionAction.getURL(self._track)))
        vars["contributionsPDFURL"]=quoteattr(str(urlHandlers.UHTrackModToPDF.getURL(self._track)))
        vars["participantListURL"]=quoteattr(str(urlHandlers.UHTrackModParticipantList.getURL(self._track)))
        totaldur = self._totaldur
        days = totaldur.days
        hours = (totaldur.seconds)/3600
        dayhours = (days * 24)+hours
        mins = ((totaldur.seconds)/60)-(hours*60)
        vars["totaldur" ]="""%sh%sm"""%(dayhours,mins)
        return vars


class WPModContribList(WPTrackModifBase):

    def _setActiveTab( self ):
        conf = self._track.getConference()
        if not conf.canModify( self._getAW() ):
            self._tabMain.disable()
            self._tabCoordination.disable()
            self._hidingTrackTabs = True
        self._tabContribs.setActive()

    def _getTabContent( self, params ):
        filterCrit=params.get("filterCrit",None)
        sortingCrit=params.get("sortingCrit",None)
        order = params.get("order","down")
        wc=WTrackModContribList(self._track,filterCrit, sortingCrit, order)
        return wc.getHTML()

class WPModParticipantList( WPTrackModifBase ):

    def __init__(self, rh, conf, emailList, displayedGroups, contribs):
        WPTrackModifBase.__init__(self, rh, conf)
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._contribs = contribs

    def _getBody( self, params ):
        WPTrackModifBase._getBody(self, params)
        wc = WContribParticipantList(self._conf, self._emailList, self._displayedGroups, self._contribs)
        params = {"urlDisplayGroup":urlHandlers.UHTrackModParticipantList.getURL(self._track)}
        return wc.getHTML(params)
