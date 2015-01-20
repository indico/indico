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

import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC import conference
from MaKaC.i18n import _

class NavigationEntry:
    _title = ""
    _url = None
    _parent = None

    @classmethod
    def getTitle(cls):
        return cls._title

    @classmethod
    def getURL(cls, *arg):
        if cls._url is not None:
            return cls._url.getURL(*arg)
        return cls._url

    @classmethod
    def getParent(cls, *arg):
        if cls._parent:
            return cls._parent()
        return None

class NEConferenceProgramme( NavigationEntry ):
    _url = urlHandlers.UHConferenceProgram
    _title = "Scientific Programme"

class NEConferenceCFA( NavigationEntry ):
    _url = urlHandlers.UHConferenceCFA
    _title = "Call for Abstracts"

class NEAbstractSubmission( NavigationEntry ):
    _url = urlHandlers.UHAbstractSubmissionDisplay
    _parent = NEConferenceCFA
    _title = "Submit a new abstract"

class NEUserAbstracts( NavigationEntry ):
    _url = urlHandlers.UHUserAbstracts
    _parent = NEConferenceCFA
    _title = "View my abstracts"

class NEAbstractDisplay( NavigationEntry ):
    _url = urlHandlers.UHAbstractDisplay
    _parent = NEUserAbstracts
    _title = "Abstract details"

class NEContributionList( NavigationEntry ):
    _url = urlHandlers.UHContributionList
    _title = "Contribution List"

class NEAuthorIndex( NavigationEntry ):
    _url = urlHandlers.UHConfAuthorIndex
    _title = "Author Index"

class NESpeakerIndex( NavigationEntry ):
    _url = urlHandlers.UHConfSpeakerIndex
    _title = "Speaker Index"


class NEConferenceTimeTable( NavigationEntry ):
    _url = urlHandlers.UHConferenceTimeTable
    _title = "Timetable"


class NESessionDisplay( NavigationEntry ):
    _url = urlHandlers.UHSessionDisplay
    _parent = NEConferenceTimeTable
    _title = "Session details"

class NEContributionDisplay( NavigationEntry ):
    _url = urlHandlers.UHContributionDisplay
    _parent = {"session": NESessionDisplay, \
               "event": NEConferenceTimeTable}
    _title = "Contribution details"

    def getParent(cls, target):
        nextPage = None
        if target is not None:
            parent = target.getOwner()
            if isinstance(parent, conference.Session):
                nextPage = cls._parent["session"]()
            elif isinstance(parent, conference.Conference):
                nextPage = cls._parent["event"]()
        return nextPage
    getParent = classmethod( getParent )

class NESubContributionDisplay(NavigationEntry):
    _url = urlHandlers.UHSubContributionDisplay
    _title = "SubContribution details"

class NEMyStuff( NavigationEntry ):
    _url = urlHandlers.UHConfMyStuff
    _title = "My conference"

class NEAbstractModify( NavigationEntry ):
    _url = urlHandlers.UHAbstractModify
    _parent = NEAbstractDisplay
    _title = "Modification"

class NEAbstractWithdraw( NavigationEntry ):
    _url = urlHandlers.UHAbstractWithdraw
    _parent = NEAbstractDisplay
    _title = "Withdrawal"

class NEAbstractRecovery( NavigationEntry ):
    _url = urlHandlers.UHAbstractRecovery
    _parent = NEAbstractDisplay
    _title = "Recovery"

class NEMeetingSessionDisplay(NavigationEntry):
    _url = urlHandlers.UHSessionDisplay
    _title = "Session details"

class NEMeetingMaterialDisplay(NavigationEntry):
    _url = urlHandlers.UHMaterialDisplay
    _parent = {"session": NEMeetingSessionDisplay, \
                           "contrib": NEContributionDisplay}
    _title = "Material details"

    def getParent(cls, target):
        nextPage = None
        if target is not None:
            parent = target.getOwner()
            if isinstance(parent, conference.Session):
                nextPage = cls._parent["session"]()
            elif isinstance(parent, conference.Contribution):
                nextPage = cls._parent["contrib"]()
        return nextPage
    getParent = classmethod( getParent)



class NEMaterialDisplay( NavigationEntry ):
    _url = urlHandlers.UHMaterialDisplay
    _parent = { "contrib": NEContributionDisplay, \
                "session": NESessionDisplay }
    _title = "Material details"

    def getParent(cls, target):
        nextPage = None
        if target is not None:
            parent = target.getOwner()
            if isinstance(parent, conference.Contribution):
                nextPage = cls._parent["contrib"]()
            elif isinstance(parent, conference.Session):
                nextPage = cls._parent["session"]()
        return nextPage
    getParent = classmethod( getParent)

class NEAbstractSubmissionConfirmation( NavigationEntry ):
    _url = urlHandlers.UHAbstractSubmissionConfirmation
    _parent = NEConferenceCFA
    _title = "Abstract submission confirmation"


class NERegistrationForm( NavigationEntry ):
    _url = urlHandlers.UHConfRegistrationForm
    _title = "Registration"

class NERegistrationFormDisplay( NavigationEntry ):
    _url = urlHandlers.UHConfRegistrationFormDisplay
    _parent = NERegistrationForm
    _title = "Registration form display"

class NERegistrationFormModify( NavigationEntry ):
    _url = urlHandlers.UHConfRegistrationFormModify
    _parent = NERegistrationForm
    _title = "Registration form modification"

class NEEvaluationMainInformation( NavigationEntry ):
    _url = urlHandlers.UHConfEvaluationMainInformation
    _title = "Evaluation"

class NEEvaluationDisplay( NavigationEntry ):
    _url = urlHandlers.UHConfEvaluationDisplay
    _parent = NEEvaluationMainInformation
    _title = "Evaluation form display"

class NEEvaluationDisplayModif( NavigationEntry ):
    _url = urlHandlers.UHConfEvaluationDisplayModif
    _parent = NEEvaluationMainInformation
    _title = "Evaluation form modification"

class NEAuthorDisplay( NavigationEntry ):
    _url = urlHandlers.UHContribAuthorDisplay
    _parent = NEAuthorIndex
    _title = "Author Display"

class NETimeTableCustomizePDF( NavigationEntry ):
    _url = urlHandlers.UHConfTimeTableCustomizePDF
    _parent = NEConferenceTimeTable
    _title = "Customize PDF"

class NEAbstractBookCustomise( NavigationEntry ):
    _url = urlHandlers.UHConfTimeTableCustomizePDF
    _title = "Customize Book of Abstracts"

class NESubContributionDisplay(NavigationEntry):
    _url = urlHandlers.UHSubContributionDisplay
    _title = "SubContribution details"
