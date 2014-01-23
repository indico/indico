# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase, WCSCSSBase, \
    CollaborationTools
from MaKaC.plugins.Collaboration.RecordingManager.common import getTalks, getOrphans
from MaKaC.plugins.Collaboration.RecordingManager.exceptions import RecordingManagerException
from indico.util.contextManager import ContextManager
import re
from indico.core.index import Catalog
#from MaKaC.common.logger import Logger

class WNewBookingForm(WCSPageTemplateBase):

    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )

        resultGetOrphans = getOrphans()
        if resultGetOrphans["success"] == True:
            orphans = resultGetOrphans["result"]
        else:
            raise RecordingManagerException(resultGetOrphans["result"])

        vars["Orphans"] = orphans
        talks = getTalks(self._conf, sort = True)
        vars["Talks"] = talks
        vars["Conference"] = self._conf
        previewURL = CollaborationTools.getOptionValue("RecordingManager", "micalaPreviewURL")
        if self._rh.use_https():
            previewURL = previewURL.replace("http","https")
        vars["PreviewURL"] = previewURL

        langPrimary = CollaborationTools.getOptionValue("RecordingManager", "languageCodePrimary")
        langSecondary = CollaborationTools.getOptionValue("RecordingManager", "languageCodeSecondary")
        langDict = CollaborationTools.getOptionValue("RecordingManager", "languageDictionary")
        (vars["FlagLanguageDataOK"], vars["LanguageErrorMessages"]) = \
            self._checkLanguageData(langPrimary, langSecondary, langDict)
        vars["LanguageCodePrimary"]   = langPrimary
        vars["LanguageCodeSecondary"] = langSecondary
        vars["LanguageDictionary"]    = langDict
        vars["LanguageCodes"]         = sorted(CollaborationTools.getOptionValue("RecordingManager", "languageDictionary").keys())
        vars["manager"] = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        return vars

    def _checkLanguageData(self, langPrimary, langSecondary, langDict):
        success = True
        messageList = []

        # regular expression to match 3 lowercase chars only (when used with match())
        patternLanguageCode = re.compile('[a-z][a-z][a-z]$')
        # regular expression to match a capitalized word with at least two chars, followed by anything
        patternLanguageName = re.compile('[A-Z].*$')

        # Make sure primary code is 3 lowercase chars
        if patternLanguageCode.match(langPrimary):
            # Make sure primary code has a key-value pair in langDict,
            # and that the language name is a capitalized word
            if langPrimary in langDict:
                if not patternLanguageName.match(langDict[langPrimary]):
                    messageList.append(_("primary language name '%s' must be a capitalized word") % langDict[langPrimary])
                    success = False
            else:
                messageList.append(_("primary language code '%s' not found in user-defined language dictionary") % langPrimary)
                success = False
        # If it's not 3 chars, don't even try to look it up.
        else:
            messageList.append(_("primary language code '%s' must be a MARC-compliant code (3 lowercase characters)") % langPrimary)
            success = False

        # Make sure secondary code is 3 lowercase chars
        if patternLanguageCode.match(langSecondary):
            # Make sure primary code has a key-value pair in langDict
            # and that the language name is a capitalized word
            if langSecondary in langDict:
                if not patternLanguageName.match(langDict[langSecondary]):
                    messageList.append(_("secondary language name '%s' must be a capitalized word") % langDict[langSecondary])
                    success = False
            else:
                messageList.append(_("secondary language code '%s' not found in user-defined language dictionary") % langSecondary)
                success = False
        # If it's not 3 chars, don't even try to look it up.
        else:
            messageList.append(_("secondary language code '%s' must be a MARC-compliant code (3 lowercase characters)") % langSecondary)
            success = False

        # Loop through keys of langDict
        for langCode in langDict.keys():
            # Make sure primary code is 3 lowercase chars
            if not patternLanguageCode.match(langCode):
                success = False

            # Make sure each key has a value:
            if langCode in langDict:
                if not patternLanguageName.match(langDict[langCode]):
                    messageList.append(_("language name '%s' must be a capitalized word") % langDict[langCode])
                    success = False
            else:
                messageList.append(_("language code '%s' not found in user-defined language dictionary") % langCode)
                success = False

        return (success, messageList)

class WMain (WJSBase):
    pass

class WIndexing(WJSBase):
    pass

class WExtra (WJSBase):
    def getVars(self):
        vars = WJSBase.getVars( self )

        if self._conf:
            vars["ConferenceId"] = self._conf.getId()
        else:
            # this is so that template can still be rendered in indexes page...
            # if necessary, we should refactor the Extra.js code so that it gets the
            # conference data from the booking, now that the booking has the conference inside
            vars["ConferenceId"] = ""
        return vars

class WStyle (WCSCSSBase):
    pass
