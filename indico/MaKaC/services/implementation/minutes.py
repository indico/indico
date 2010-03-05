from MaKaC.services.implementation.base import ParameterManager, TextModificationBase
from MaKaC.services.implementation.base import ProtectedModificationService

from MaKaC import conference
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.utils import isStringHTML,sortContributionByDate
import MaKaC.webinterface.locators as locators



class MinutesEdit(TextModificationBase, ProtectedModificationService):

    def _checkParams(self):
        ProtectedModificationService._checkParams(self)

        pm = ParameterManager(self._params)

        l = locators.WebLocator()

        # TODO: This chain could (should) be repalced by a more generic
        # locator, something like:
        # l.setParams(self._params)
        # l.getObject() # retrieves whatever object has been extracted

        # will check cotnribution and session as well, as fallback cases
        l.setSubContribution( self._params, 0 )
        # will check if it is compiling minutes
        self._compile = self._params.get("compile", False)

        self._target = l.getObject()

        # TODO: change str to some kind of html sanitization
        self._text = pm.extract("value", pType=str, allowEmpty=True)

    def _checkProtection(self):
        if (type(self._target) == conference.Session and \
               not self._target.canCoordinate(self.getAW())) or \
               (type(self._target) == conference.Contribution and \
                not self._target.canUserSubmit(self._getUser())):
            ProtectedModificationService._checkProtection(self);

    def _handleSet(self):

        # Account for possible retries (due to conflicts)
        # If 'minutesFileId' is defined, there was a previous try
        fileId = ContextManager.getdefault('minutesFileId', None)

        minutes = self._target.getMinutes()
        if not minutes:
            minutes = self._target.createMinutes()
        minutes.setText( self._text, forcedFileId=fileId)

        # save the fileId, in case there is a conflict error
        # in the worst case scenario the file will be rewritten multiple times
        res = minutes.getResourceById('minutes')
        ContextManager.set('minutesFileId', res.getRepositoryId())


    def _handleGet(self):
        if self._compile:
            return self._getCompiledMinutes()
        minutes = self._target.getMinutes()
        if not minutes:
            return None
        else:
            return minutes.getText()

    def _getCompiledMinutes( self ):
        minutes = []
        isHTML = False
        cList = self._target.getContributionList()
        cList.sort(sortContributionByDate)
        for c in cList:
            if c.getMinutes():
                minText = c.getMinutes().getText()
                minutes.append([c.getTitle(),minText])
                if isStringHTML(minText):
                    isHTML = True
        if isHTML:
            lb = "<br>"
        else:
            lb = "\n"
        text = "%s (%s)%s" % (self._target.getTitle(), self._target.getStartDate().strftime("%d %b %Y"), lb)
        part = self._target.getParticipation().getPresentParticipantListText()
        if part != "":
            text += "Present: %s%s" % (part,lb)
        uList = self._target.getChairList()
        chairs = ""
        for chair in uList:
            if chairs != "":
                chairs += "; "
            chairs += chair.getFullName()
        if len(uList) > 0:
            text += "Chaired by: %s%s%s" % (chairs, lb, lb)
        for min in minutes:
            text += "==================%s%s%s==================%s%s%s%s" % (lb,min[0],lb,lb,min[1],lb,lb)

        return text

methodMap = {
    "edit": MinutesEdit
    }
