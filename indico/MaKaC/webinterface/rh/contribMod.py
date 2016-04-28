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

from cStringIO import StringIO

from indico.web.flask.util import send_file

import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.contributions as contributions
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.common.xmlGen import XMLGen
from MaKaC.common.utils import parseDateTime
from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase
from MaKaC.PDFinterface.conference import ContribToPDF



class RHContribModifBase(RHModificationBaseProtected):
    """ Base RH for contribution modification.
        Sets the _target (the contribution) and the _conf (the conference)
    """

    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setContribution(params)
        self._target = l.getObject()
        self._conf = self._target.getConference()

    def getWebFactory(self):
        wr = webFactoryRegistry.WebFactoryRegistry()
        self._wf = wr.getFactory(self._target.getConference())
        return self._wf

class RCSessionCoordinator(object):
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a Session Coordinator
        """
        if request._target.getSession() != None:
            return request._target.getSession().canCoordinate(request.getAW(), "modifContribs")
        else:
            return False

class RCContributionPaperReviewingStaff(object):

    @staticmethod
    def hasRights(request, contribution = None, includingContentReviewer=True):
        """ Returns true if the user is a PRM, or a Referee / Editor / Reviewer of the target contribution
        """
        user = request.getAW().getUser()
        confPaperReview = request._target.getConference().getConfPaperReview()
        paperReviewChoice = confPaperReview.getChoice()
        if contribution:
            reviewManager = confPaperReview.getReviewManager(contribution)
        else:
            reviewManager = confPaperReview.getReviewManager(request.contrib)
        return (confPaperReview.isPaperReviewManager(user) or \
               (reviewManager.hasReferee() and reviewManager.isReferee(user)) or \
               ((paperReviewChoice == 3 or paperReviewChoice == 4) and reviewManager.hasEditor() and reviewManager.isEditor(user)) or \
               (includingContentReviewer and ((paperReviewChoice == 2 or paperReviewChoice == 4) and reviewManager.isReviewer(user))))

class RCContributionReferee(object):
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a referee of the target contribution
        """
        user = request.getAW().getUser()
        reviewManager = request.contrib.event_new.as_legacy.getReviewManager(request.contrib)
        return reviewManager.hasReferee() and reviewManager.isReferee(user)

class RCContributionEditor(object):
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is an editor of the target contribution
        """

        user = request.getAW().getUser()
        reviewManager = request._conf.getReviewManager(request.contrib)
        return reviewManager.hasEditor() and reviewManager.isEditor(user)

class RCContributionReviewer(object):
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a reviewer of the target contribution
        """
        user = request.getAW().getUser()
        reviewManager = request._conf.getReviewManager(request.contrib)
        return reviewManager.isReviewer(user)

class RHContribModifBaseSpecialSesCoordRights(RHContribModifBase):
    """ Base class for any RH where a Session Coordinator has the rights to perform the request
    """

    def _checkProtection(self):
        if not RCSessionCoordinator.hasRights(self):
            RHContribModifBase._checkProtection(self)

class RHContribModifBaseSpecialSesCoordAndReviewingStaffRights(RHContribModifBase):
    """ Base class for any RH where a member of the Paper Reviewing staff
        (a PRM, or a Referee / Editor / Reviewer of the target contribution),
        OR  a Session Coordinator has the rights to perform the request
    """

    def _checkProtection(self):
        if not (RCSessionCoordinator.hasRights(self) or RCContributionPaperReviewingStaff.hasRights(self)):
            RHContribModifBase._checkProtection(self);

class RHContributionModification(RHContribModifBaseSpecialSesCoordAndReviewingStaffRights):
    _uh = urlHandlers.UHContributionModification

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]

    def _process(self):
        params = self._getRequestParams()
        if self._target.getOwner().isClosed():
            p = contributions.WPContributionModificationClosed(self, self._target)
        else:
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContributionModification(self, self._target)
            else:
                p = contributions.WPContributionModification(self, self._target)
        return p.display(**params)

class RHWithdraw(RHContribModifBaseSpecialSesCoordRights):
    _uh=urlHandlers.UHContribModWithdraw

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._action=""
        self._comment=""
        if params.has_key("REACTIVATE"):
            self._action="REACTIVATE"
        elif params.has_key("OK"):
            self._action="WITHDRAW"
            self._comment=params.get("comment", "")
        elif params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process(self):
        url=urlHandlers.UHContributionModification.getURL(self._target)
        if self._action=="REACTIVATE":
            self._target.withdraw(self._getUser(), self._comment)
            self._redirect(url)
            return
        elif self._action=="WITHDRAW":
            self._target.withdraw(self._getUser(), self._comment)
            self._redirect(url)
            return
        elif self._action=="CANCEL":
            self._redirect(url)
            return
        p=contributions.WPModWithdraw(self, self._target)
        return p.display()


class RHContributionAC(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribModifAC

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]

    def _process(self):
        params = self._getRequestParams()
        if self._target.getOwner().isClosed():
            p = contributions.WPContributionModificationClosed(self, self._target)
        else:
            p = contributions.WPContribModifAC(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContribModifAC(self, self._target)
        return p.display(**params)


#-------------------------------------------------------------------------------------

class RHContributionTools(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribModifTools

    def _process(self):
        if self._target.getOwner().isClosed():
            p = contributions.WPContributionModificationClosed(self, self._target)
        else:
            p = contributions.WPContributionModifTools(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContributionModifTools(self, self._target)
        return p.display()


class RHContributionData(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionDataModif

    def _checkParams( self, params ):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)

        self._evt = self._target

    def _process(self):
        if self._target.getOwner().isClosed():
            p = contributions.WPContributionModificationClosed(self, self._target)
        else:
            p = contributions.WPEditData(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContributionEditData(self, self._target)
        return p.display(**self._getRequestParams())


class RHContributionModifData(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionDataModification

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._type=None
        self._check = int(params.get("check", 1))
        if params.has_key("type") and params["type"].strip()!="":
            self._type=self._target.getConference().getContribTypeById(params["type"])
        self._cancel = params.has_key("cancel")

    def _process(self):
        if not self._cancel:
            params = self._getRequestParams()

            if params.has_key("dateTime"):
                dateTime = parseDateTime(params["dateTime"])
                params["sYear"] = dateTime.year
                params["sMonth"] = dateTime.month
                params["sDay"] = dateTime.day
                params["sHour"] = dateTime.hour
                params["sMinute"] = dateTime.minute
            else:
                params["sYear"] = ""
                params["sMonth"] = ""
                params["sDay"] = ""
                params["sHour"] = ""
                params["sMinute"] = ""

            if params.has_key("duration"):
                params["durMins"] = params["duration"];
            else:
                params["durMins"] = ""
            self._target.setValues(params)
            self._target.setType(self._type)
        self._redirect(urlHandlers.UHContributionModification.getURL(self._target))


class RHSetTrack(RHContribModifBase):

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._track=None
        if params.has_key("selTrack") and params["selTrack"].strip() != "":
            self._track = self._target.getConference().getTrackById(params["selTrack"])

    def _process(self):
        self._target.setTrack(self._track)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)


class RHSetSession(RHContribModifBase):

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._session=None
        if params.has_key("selSession") and params["selSession"].strip() != "":
            self._session=self._target.getConference().getSessionById(params["selSession"])

    def _process(self):
        self._target.setSession(self._session)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)


class RHMaterialsAdd(RHSubmitMaterialBase, RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribModifAddMaterials

    def __init__(self):
        RHContribModifBaseSpecialSesCoordRights.__init__(self)
        RHSubmitMaterialBase.__init__(self)

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        RHSubmitMaterialBase._checkParams(self, params)

    def _checkProtection(self):
        material, _ = self._getMaterial(forceCreate = False)
        if self._target.canUserSubmit(self._aw.getUser()) \
            and (not material or material.getReviewingState() < 3):
            self._loggedIn = True
        # status = 3 means the paper is under review (submitted but not reviewed)
        # status = 2 means that the author has not yet submitted the material
        elif not (RCContributionPaperReviewingStaff.hasRights(self, includingContentReviewer=False)
                  and self._target.getReviewing() and self._target.getReviewing().getReviewingState() in (2, 3)):
            RHSubmitMaterialBase._checkProtection(self)
        else:
            self._loggedIn = True

    def _process(self):
        result = RHSubmitMaterialBase._process(self)
        # if a Paper Reviewer uploads a paper, when the status is 'To be corrected', we must change the status to 'Submitted' again.
        if self._target.getReviewing() and self._target.getReviewing().getReviewingState() == 2 and RCContributionPaperReviewingStaff.hasRights(self, includingContentReviewer=False):
            self._target.getReviewManager().getLastReview().setAuthorSubmitted(True)
        return result


class RHContributionSetVisibility(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionSetVisibility

    def _process(self):
        params = self._getRequestParams()
        if params.has_key("changeToPrivate"):
            self._protect = 1
        elif params.has_key("changeToInheriting"):
            self._protect = 0
        elif params.has_key("changeToPublic"):
            self._protect = -1
        self._target.setProtection(self._protect)
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))

class RHContributionDeletion(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionDelete

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._cancel = False
        if "cancel" in params:
            self._cancel = True
        self._confirmation = params.has_key("confirm")

    def _perform(self):
        conf = self._target.getConference()
        self._target.getOwner().getSchedule().removeEntry(self._target.getSchEntry())
        #self._target.getOwner().removeContribution(self._target)
        self._target.delete()
        #conf.removeContribution(self._target)

    def _process(self):
        if self._cancel:
            self._redirect(urlHandlers.UHContribModifTools.getURL(self._target))
        elif self._confirmation:
            owner = self._target.getOwner()
            self._perform()
            if self._target.getSession():
                self._redirect(urlHandlers.UHSessionModification.getURL(owner))
            else:
                self._redirect(urlHandlers.UHConferenceModification.getURL(owner))
        else:
            p = contributions.WPContributionDeletion(self, self._target)
            return p.display()


class RHContributionToXML(RHContributionModification):
    _uh = urlHandlers.UHContribToXMLConfManager

    def _process(self):
        filename = "%s - contribution.xml"%self._target.getTitle()
        x = XMLGen()
        x.openTag("contribution")
        x.writeTag("Id", self._target.getId())
        x.writeTag("Title", self._target.getTitle())
        x.writeTag("Description", self._target.getDescription())
        afm = self._target.getConference().getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getFields():
            id = f.getId()
            if f.isActive() and str(self._target.getField(id)).strip() != "":
                x.writeTag(f.getCaption().replace(" ", "_"), self._target.getField(id))
        x.writeTag("Conference", self._target.getConference().getTitle())
        session = self._target.getSession()
        if session!=None:
            x.writeTag("Session", self._target.getSession().getTitle())
        l = []
        for au in self._target.getAuthorList():
            if self._target.isPrimaryAuthor(au):
                x.openTag("PrimaryAuthor")
                x.writeTag("FirstName", au.getFirstName())
                x.writeTag("FamilyName", au.getFamilyName())
                x.writeTag("Email", au.getEmail())
                x.writeTag("Affiliation", au.getAffiliation())
                x.closeTag("PrimaryAuthor")
            else:
                l.append(au)

        for au in l:
            x.openTag("Co-Author")
            x.writeTag("FirstName", au.getFirstName())
            x.writeTag("FamilyName", au.getFamilyName())
            x.writeTag("Email", au.getEmail())
            x.writeTag("Affiliation", au.getAffiliation())
            x.closeTag("Co-Author")

        for au in self._target.getSpeakerList():
            x.openTag("Speaker")
            x.writeTag("FirstName", au.getFirstName ())
            x.writeTag("FamilyName", au.getFamilyName())
            x.writeTag("Email", au.getEmail())
            x.writeTag("Affiliation", au.getAffiliation())
            x.closeTag("Speaker")

        #To change for the new contribution type system to:
        typeName = ""
        if self._target.getType():
            typeName = self._target.getType().getName()
        x.writeTag("ContributionType", typeName)

        t = self._target.getTrack()
        if t!=None:
            x.writeTag("Track", t.getTitle())

        x.closeTag("contribution")

        return send_file(filename, StringIO(x.getXml()), 'XML')


class RHContributionToPDF(RHContributionModification):
    _uh = urlHandlers.UHContribToPDFConfManager

    def _process(self):
        tz = self._target.getConference().getTimezone()
        filename = "%s - Contribution.pdf"%self._target.getTitle()
        pdf = ContribToPDF(self._target)
        return send_file(filename, pdf.generate(), 'PDF')
