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


class NEAbstractSubmissionConfirmation( NavigationEntry ):
    _url = urlHandlers.UHAbstractSubmissionConfirmation
    _parent = NEConferenceCFA
    _title = "Abstract submission confirmation"
