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

from indico.core.extpoint import IListener, IContributor


class IAccessControlListener(IListener):

    def protectionChanged(self, obj, oldProtection, newProtection):
        pass

    def accessGranted(self, obj, who):
        """
        Access was granted to a particular user/group/email
        """

    def accessRevoked(self, obj, who):
        """
        Access was revoked for a particular user/group/email
        """

    def modificationGranted(self, obj, who):
        """
        Modification was revoked for a particular user/group/email
        """


    def modificationRevoked(self, obj, who):
        """
        Modification was revoked for a particular user/group/email
        """

    def accessDomainAdded(self, obj, domain):
        pass

    def accessDomainRemoved(self, obj, domain):
        pass


class ITimeActionListener(IListener):

    def dateChanged(self, obj, oldDate, newDate):
        pass

    def startDateChanged(self, obj, oldSdate, sdate):
        pass

    def endDateChanged(self, obj, oldEdate, edate):
        pass

    def startTimeChanged(self, obj, oldSdate, sdate):
        pass

    def endTimeChanged(self, obj, oldEdate, edate):
        pass

    def eventDatesChanged(self, obj, oldStartDate, oldEndDate,
                          newStartDate, newEndDate):
        pass

    def timezoneChanged(self, obj, oldTimezone, timezone):
        pass

    def contributionUnscheduled(self, obj):
        pass

    def contributionScheduled(self, contrib):
        pass

class IObjectLifeCycleListener(IListener):

    def created(self, obj, owner):
        pass

    def moved(self, obj, fromOwner, toOwner):
        pass

    def deleted(self, obj, oldOwner):
        pass


class IMetadataChangeListener(IListener):

    def categoryTitleChanged(self, obj, oldTitle, newTitle):
        pass

    def eventTitleChanged(self, obj, oldTitle, newTitle):
        pass

    def contributionTitleChanged(self, obj, oldTitle, newTitle):
        pass

    def infoChanged(self, obj):
        pass


class IMaterialDownloadListener(IListener):

    def materialDownloaded(self, obj):
        """
        Listens for material downloaded, to be handled by (for example) tracking
        applications.
        """
        pass


class ITimetableContributor(IContributor):
    """
    Encapsulates extension points concerning event timetable.
    """

    def includeTimetableJSFiles(self, obj, params = {}):
        """
        Includes additional JS files.
        """

    def includeTimetableCSSFiles(self, obj, params = {}):
        """
        Includes additional Css files.
        """

    def customTimetableLinks(self, obj, params = {}):
        """
        Inserts additional links inside the timetable's header.
        """


class INavigationContributor(IContributor):
    """
    Events that fill the sidemenu of a conference with the activated plugins.
    You may want a reference to know how to implement these methods.
    You can check the components file for XMPP (MaKaC.plugins.InstantMessaging.XMPP)
    """

    #Conference management related
    def fillManagementSideMenu(self, obj, params):
        """
        Inserts an element in the conference management's side menu
        """

    #Conference display related
    def confDisplaySMFillDict(self, obj, params):
        """
        Conference Display Side Menu Fill Dictionary.
        This dictionary is used to store all your new items on the side menu of the conference display.
        In the core, there is a dictionary called self._linkData in which the elements to be showed
        in the conference display side menu are inserted.
        """

    #Conference display related
    def confDisplaySMFillOrderedKeys(self, obj, list):
        """
        Conference Display Side Menu Fill Ordered Keys.
        Right next to the dictionary there is a list with the ordered keys,
        we need to include them also
        """

    #Conference display related
    def confDisplaySMShow(self, obj, params):
        """
        Adds our element to the list of elements to be showed in the side menu of the
        conference main page
        """

    #Conference display related

    def fillConferenceHeader(self, obj, params):
        """
        Inserts an element in the conference header
        """
        pass

    #Meetings and lectures display related
    def meetingAndLectureDisplay(self, obj, params):
        """
        Adds our element to the list of elements to be showed in the main menu of a
        meeting or a lecture
        """

    #Event cloning related
    def addCheckBox2CloneConf(self, obj, list):
        """
        Adds a checkbox in the page to clone an event. When an event is cloned,
        you may want to clone part of your plugin data. In this method you will
        add a checkbox to the list in case it's necessary
        """

    #Event cloning related
    def fillCloneDict(self, obj, params):
        """
        Fills a dictionary with the checkboxes to be checked when cloning an event
        """

    #Event cloning related
    def cloneEvent(self, confToClone, conf):
        """
        Performs the operations needed while cloning an event
        """

    def getActiveNavigationItem(self, obj, params):
        pass

    #Category Header related

    def fillCategoryHeader(self, obj, params):
        """
        Inserts an element in the category header
        """
        pass


    def includeMainJSFiles(self, obj):
        """
        Observers should contribute with JS files they wish to add
        """

class IEventDisplayContributor(IContributor):

    """
    Aggregates extension points that relate to event display pages
    """

    def injectCSSFiles(self, obj):
        """
        Observers should contribute with CSS files they wish to add to the
        <head></head> block
        """

    def injectJSFiles(self, obj):
        """
        Observers should contribute with JS files they wish to add
        """

    def eventDetailBanner(self, obj, conf):
        """
        Returns the info that the plugins want to add after the header (where description is)
        """

    def eventDetailFooter(self, obj, vars):
        """
        Returns the info that the plugins want to add into the footer.
        """

    def detailSessionContribs(self, obj, conf, params):
        """
        Returns the info that the plugins want to add to the Sessions and Contributions
        """

    def addXMLMetadata(self, obj, params):
        """
        Adds to the output generator the XML we want to add
        """

class IUserAreaContributor(IContributor):
    """
    Aggregates extension points that relate to the user area pages
    """
    def userPreferences(self, obj, userId):
        """
        Returns the preferences that the plugins want to add in user profile preferences
        """

class IHeaderContributor(IContributor):
    """
    Aggregates extension points that relate to the user area pages
    """
    def addParamsToHeaderItem(self, obj, itemList):
        """
        Returns the preferences that the plugins want to add in user profile preferences
        """

