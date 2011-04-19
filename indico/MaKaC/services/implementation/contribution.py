from MaKaC.services.implementation.base import ProtectedModificationService
from MaKaC.services.implementation.base import ProtectedDisplayService
from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.roomBooking import GetBookingBase

from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError

from MaKaC.common.PickleJar import DictPickler

import MaKaC.conference as conference
from MaKaC.services.implementation.base import TextModificationBase
from MaKaC.services.implementation.base import HTMLModificationBase
from MaKaC.services.implementation.base import DateTimeModificationBase
from MaKaC.common.fossilize import fossilize
from MaKaC.user import PrincipalHolder, Avatar, Group

class ContributionBase(object):

    def _checkParams( self ):
        try:
            self._target = self._conf = conference.ConferenceHolder().getById(self._params["conference"]);
        except:
            try:
                self._target = self._conf = conference.ConferenceHolder().getById(self._params["confId"]);
            except:
                raise ServiceError("ERR-E4", "Invalid conference id.")

        if self._conf == None:
            raise Exception("Conference id not specified.")

        try:
            self._target = self._contribution = self._conf.getContributionById(self._params["contribution"])
        except:
            try:
                self._target = self._contribution = self._conf.getContributionById(self._params["contribId"])
            except:
                raise ServiceError("ERR-C0", "Invalid contribution id.")

        if self._target == None:
            raise Exception("Contribution id not specified.")

        # create a parameter manager that checks the consistency of passed parameters
        self._pm = ParameterManager(self._params)

class ContributionDisplayBase(ProtectedDisplayService, ContributionBase):

    def _checkParams(self):
        ContributionBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)

class ContributionModifBase(ProtectedModificationService, ContributionBase):

    def _checkParams(self):
        ContributionBase._checkParams(self)
        ProtectedModificationService._checkParams(self)

    def _checkProtection(self):
        if self._target.getSession() != None:
            if self._target.getSession().canCoordinate(self.getAW(), "modifContribs"):
                return
        ProtectedModificationService._checkProtection(self)

class ContributionTextModificationBase(TextModificationBase, ContributionBase):
    pass

class ContributionHTMLModificationBase(HTMLModificationBase, ContributionBase):
    pass

class ContributionDateTimeModificationBase (DateTimeModificationBase, ContributionBase):
    pass

class ContributionAddSubContribution(ContributionModifBase):
    def _checkParams(self):
        ContributionModifBase._checkParams(self)

        # "presenters" and "keywords" are not required. they can be empty
        self._presenters = self._pm.extract("presenters", pType=list, allowEmpty=True)
        self._keywords = self._pm.extract("keywords", pType=list, allowEmpty=True)
        self._description = self._pm.extract("description", pType=str, allowEmpty=True, defaultValue="")
        self._reportNumbers = self._pm.extract("reportNumbers", pType=list, allowEmpty=True, defaultValue=[])
        self._materials = self._pm.extract("materials", pType=dict, allowEmpty=True)

        # these are required
        self._duration = self._pm.extract("duration", pType=int)
        self._title = self._pm.extract("title", pType=str)

    def __addPresenters(self, subcontrib):

        # add each presenter
        for presenterValues in self._presenters:

            # magically update a new ContributionParticipation with JSON data, using the DictPickler
            presenter = conference.SubContribParticipation()
            DictPickler.update(presenter, presenterValues)

            subcontrib.newSpeaker(presenter)

    def __addMaterials(self, subcontrib):
        if self._materials:
            for material in self._materials.keys():
                newMaterial = conference.Material()
                newMaterial.setTitle(material)
                for resource in self._materials[material]:
                    newLink = conference.Link()
                    newLink.setURL(resource)
                    newLink.setName(resource)
                    newMaterial.addResource(newLink)
                subcontrib.addMaterial(newMaterial)

    def __addReportNumbers(self, subcontrib):
        if self._reportNumbers:
            for reportTuple in self._reportNumbers:
                for recordNumber in reportTuple[1]:
                    subcontrib.getReportNumberHolder().addReportNumber(reportTuple[0], recordNumber)

    def _getAnswer(self):
        # create the sub contribution
        sc = self._target.newSubContribution()

        sc.setTitle( self._title )
        sc.setDescription( self._description )
        # separate the keywords using newlines
        sc.setKeywords('\n'.join(self._keywords))
        sc.setDuration( self._duration / 60, \
                         self._duration % 60 )

        self.__addMaterials(sc)
        self.__addReportNumbers(sc)
        self.__addPresenters(sc)

        # log the event
        logInfo = sc.getLogInfo()
        logInfo["subject"] = "Create new subcontribution: %s"%sc.getTitle()
        self._target.getConference().getLogHandler().logAction(logInfo, "Timetable/SubContribution", self._getUser())

class ContributionDeleteSubContribution(ContributionModifBase):

    # contribution.deleteSubContribution

    _asyndicoDoc = {
        'summary':  'Deletes a subcontribution, given the conference, contribution and subcontribution IDs.',
        'params': [{'name': 'conference', 'type': 'str'},
                   {'name': 'contribution', 'type': 'str'},
                   {'name': 'subcontribution', 'type': 'str'}],
        'return': None
        }

    def _checkParams(self):
        ContributionModifBase._checkParams(self)

        subContId = self._pm.extract("subcontribution", pType=str, allowEmpty=False)

        self._subContribution = self._contribution.getSubContributionById(subContId)

    def _getAnswer(self):
        self._subContribution.getOwner().removeSubContribution(self._subContribution)

class ContributionGetBooking(ContributionDisplayBase, GetBookingBase):
    pass

class ContributionProtectionUserList(ContributionModifBase):

    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._contribution.getAllowedToAccessList())

class ContributionProtectionAddUsers(ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)

        self._usersData = self._params['value']
        self._user = self.getAW().getUser()

    def _getAnswer(self):

        for user in self._usersData :

            userToAdd = PrincipalHolder().getById(user['id'])

            if not userToAdd :
                raise ServiceError("ERR-U0","User does not exist!")

            self._contribution.grantAccess(userToAdd)

class ContributionProtectionRemoveUser(ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)

        self._userData = self._params['value']

        self._user = self.getAW().getUser()

    def _getAnswer(self):

        userToRemove = PrincipalHolder().getById(self._userData['id'])

        if not userToRemove :
            raise ServiceError("ERR-U0","User does not exist!")
        elif isinstance(userToRemove, Avatar) or isinstance(userToRemove, Group) :
            self._contribution.revokeAccess(userToRemove)

methodMap = {
    "addSubContribution": ContributionAddSubContribution,
    "deleteSubContribution": ContributionDeleteSubContribution,
    "getBooking": ContributionGetBooking,
    "protection.getAllowedUsersList": ContributionProtectionUserList,
    "protection.addAllowedUsers": ContributionProtectionAddUsers,
    "protection.removeAllowedUser": ContributionProtectionRemoveUser
}
