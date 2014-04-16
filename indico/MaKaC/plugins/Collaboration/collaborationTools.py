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

import pkg_resources, sys
from MaKaC.plugins import PluginsHolder, Plugin
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.common.contribFilters import PosterFilterField
from MaKaC.common.utils import formatDateTime, formatTwoDates, formatTime, formatDuration
from MaKaC.common.timezoneUtils import getAdjustedDate, isSameDay, minDatetime
from indico.core.config import Config
from MaKaC.conference import Contribution, Conference
from MaKaC.plugins.Collaboration.fossils import ICSBookingBaseIndexingFossil, \
    IQueryResultFossil, ICSBookingInstanceIndexingFossil
from MaKaC.fossils.conference import IConferenceFossil
from MaKaC.common.contextManager import ContextManager
from indico.core.index import Catalog


class CollaborationTools(object):
    """ Class with utility classmethods for the Collaboration plugins core and plugins
    """

    #This commented code tried to gain some performance by caching the collaboration
    # PluginType object, but sometimes there would be problems by
    # different requests sharing memory and trying to access the database
    # after a connection was closed. This happened under Apache in Windows Vista with ZODB 3.8
#    _cpt = None
#    _plugins = {}

    @classmethod
    def getCollaborationPluginType(cls):
        #This commented code tried to gain some performance by caching the collaboration
        # PluginType object, but sometimes there would be problems by
        # different requests sharing memory and trying to access the database
        # after a connection was closed. This happened under Apache in Windows Vista with ZODB 3.8
#        if not cls._cpt:
#            cls._cpt = PluginsHolder().getPluginType("Collaboration")
#        return cls._cpt
        return PluginsHolder().getPluginType("Collaboration")

    @classmethod
    def getPlugin(cls, pluginId):
        #This commented code tried to gain some performance by caching the collaboration
        # PluginType object, but sometimes there would be problems by
        # different requests sharing memory and trying to access the database
        # after a connection was closed. This happened under Apache in Windows Vista with ZODB 3.8

#        if not pluginName in cls._plugins:
#            cls._plugins[pluginName] = cls.getCollaborationPluginType().getPlugin(pluginId)
#        return cls._plugins[pluginId]
        return cls.getCollaborationPluginType().getPlugin(pluginId)

    @classmethod
    def anyPluginsAreActive(cls):
        return len(cls.getCollaborationPluginType().getPlugins(includeNonActive = False)) > 0

    @classmethod
    def getOptionValue(cls, pluginId, optionName):
        """ Returns the value of an option of a plugin (plugins/Collaboration/XXXXX/options.py)
            pluginName: a string with the name of the plugin
            optionName: a string with the name of the option
        """
        return cls.getCollaborationPluginType().getPlugin(pluginId).getOption(optionName).getValue()

    @classmethod
    def getOptionValueRooms(cls, pluginId, optionName):
        """ Returns the room list of an option with type 'rooms' of a plugin (plugins/Collaboration/XXXXX/options.py)
            pluginName: a string with the name of the plugin
            optionName: a string with the name of the option
        """
        return cls.getCollaborationPluginType().getPlugin(pluginId).getOption(optionName).getRooms()

    @classmethod
    def hasOption(cls, pluginId, optionName):
        return cls.getCollaborationPluginType().getPlugin(pluginId).hasOption(optionName)

    @classmethod
    def hasCollaborationOption(cls, optionName):
        return cls.getCollaborationPluginType().hasOption(optionName)

    @classmethod
    def getCollaborationOptionValue(cls, optionName):
        """ Returns the value of an option of the Collaboration plugin type (plugins/Collaboration/options.py)
        """
        return cls.getCollaborationPluginType().getOption(optionName).getValue()

    @classmethod
    def getModule(cls, pluginId):
        """ Utility function that returns a module object given a plugin name.
            pluginId: a string such as "evo", "DummyPlugin", etc.
        """
        pmodules = pkg_resources.get_entry_map('indico', group='indico.ext')
        entry = pmodules.get('Collaboration.%s' % pluginId, None)
        if entry:
            __import__(entry.module_name, globals(), locals(),
                       ['collaboration', 'pages', 'actions', 'fossils', 'services'])
            return sys.modules[entry.module_name]
        else:
            return None

    @classmethod
    def getTemplateClass(cls, pluginId, templateName):
        """ Utility function that returns a template class object given a plugin name and the class name.
            Example: templateClass = CollaborationTools.getTemplateClass("EVO", "WNewBookingForm") will return the WNewBookingForm class in the EVO plugin.
        """
        return cls.getModule(pluginId).pages.__dict__.get(templateName, None)

    @classmethod
    def getServiceClass(cls, pluginName, serviceName):
        """ Utility function that returns a service class object given a plugin name and the class name.
            Example: serviceClass = CollaborationTools.getTemplateClass("WebcastRequest", "WebcastAbleTalksService") will return the WebcastAbleTalksService class in the WebcastRequest plugin.
        """
        return cls.getModule(pluginName).services.__dict__.get(serviceName + "Service", None)

    @classmethod
    def getGlobalData(cls, pluginName):
        """ Returns the GlobalData object of a plugin
        """
        return cls.getPlugin(pluginName).getGlobalData()

    @classmethod
    def getExtraJS(cls, conf, plugin, user):
        """ Utility function that returns a string with the extra JS declared by a plugin.
        """
        templateClass = cls.getTemplateClass(plugin.getId(), "WExtra")
        if templateClass:
            return templateClass(conf, plugin.getId(), user).getHTML()
        else:
            return None

    @classmethod
    def getCSBookingClass(cls, pluginName):
        """ Utility function that returns a CSBooking class given a plugin name.
            Example: templateClass = getCSBookingClass("EVO") will return the CSBooking class of the EVO plugin.
        """
        return cls.getModule(pluginName).collaboration.CSBooking

    @classmethod
    def getTabs(cls, conference, user):
        """ Returns a list of tab names corresponding to the active plugins for an event.
            If a user is specified, only tabs that a user can see are returned.
            A user can see a tab if:
            -The user is a Server Admin or a Video Services Admin
            -The user is a Plugin Admin of a plugin in that tab.
            -The user is an Event Manager or Video Services Manager and the plugin is not "admins only"
            -The user is a Plugin Manager of a plugin in that tab and the plugin is not "admins only"
        """
        tabNamesSet = set()

        csbm = Catalog.getIdx("cs_bookingmanager_conference").get(conference.getId())

        # we get the list of Plugin objects allowed for this kind of event
        if csbm is not None:
            allowedForThisEvent = csbm.getAllowedPlugins()

            for plugin in allowedForThisEvent:

                if cls.canUserManagePlugin(conference, plugin, user):
                    tabNamesSet.add(cls.getPluginTab(plugin))
                    EATab = cls.getEATab(plugin)
                    if EATab is not None:
                        tabNamesSet.add(EATab)

        tabNames = list(tabNamesSet)
        return tabNames

    @classmethod
    def getPluginTab(cls, pluginObject):
        """ Utility function that returns the tab a Collaboration plugin belongs to.
            If the option was not defined, "Collaboration" is the default.
        """
        if pluginObject.hasOption("tab"):
            return pluginObject.getOption("tab").getValue()
        else:
            return "Collaboration"

    @classmethod
    def getEATab(cls, pluginObject):
        """ Utility function that returns the Electronic Agreement Tab
            (to be defined in options.py of each plugin that need it) a Collaboration plugin belongs to.
            If the option was not defined, None is returned.
        """
        if pluginObject.hasOption("ElectronicAgreementTab"):
            return pluginObject.getOption("ElectronicAgreementTab").getValue()
        else:
            return None

    @classmethod
    def getPluginsByTab(cls, tabName, conference, user):
        """ Utility function that returns a list of plugin objects.
            These Plugin objects will be of the "Collaboration" type, and only those who have declared a subtab equal
            to the "tabName" argument will be returned.
            If tabName is None, [] is returned.
            The conference object is used to filter plugins that are not allowed in a conference,
            because of the conference type or the equipment of the conference room
            If a user is specified, only tabs with plugins that the user can see will be returned:
            -
        """
        if tabName:

            csbm = Catalog.getIdx("cs_bookingmanager_conference").get(conference.getId())

            if conference:
                allowedPlugins = csbm.getAllowedPlugins()
            else:
                allowedPlugins = None

            #we get the plugins of this tab
            return cls.getCollaborationPluginType().getPluginList(
                doSort = True,
                filterFunction = lambda plugin: cls.getPluginTab(plugin) == tabName and
                                                (allowedPlugins is None or plugin in allowedPlugins) and
                                                cls.canUserManagePlugin(conference, plugin, user)
            )
        else:
            return []

    @classmethod
    def canUserManagePlugin(cls, conference, plugin, user):
        """ Utility function that returns if a user can interact with a plugin inside an event,
            depending on the plugin, the user, and the event where the user tries to see a plugin page
            or change a plugin object
        """

        csbm = Catalog.getIdx("cs_bookingmanager_conference").get(conference.getId())

        from MaKaC.plugins.Collaboration.handlers import RCCollaborationAdmin
        isAdminUser = RCCollaborationAdmin.hasRights(user)

        isAdminOnlyPlugin = cls.isAdminOnlyPlugin(plugin)

        canSee = (
                isAdminUser or
                user in plugin.getOption('admins').getValue() or
                not isAdminOnlyPlugin and (conference.canUserModify(user) or
                                           csbm.isVideoServicesManager(user) or
                                           csbm.isPluginManager(plugin.getName(), user) ) )

        return canSee



    @classmethod
    def splitPluginsByAllowMultiple(cls, pluginList):
        """ Utility function that returns a tuple of 2 lists of Plugin objects.
            The first list are the plugins who only allow 1 booking of their type.
            The second list are the plugins who allow multiple bookings of their type.
        """

        #we split them into 2 lists
        singleBookingPlugins = [p for p in pluginList if not cls.getCSBookingClass(p.getId())._allowMultiple]
        multipleBookingPlugins = [p for p in pluginList if cls.getCSBookingClass(p.getId())._allowMultiple]

        return singleBookingPlugins, multipleBookingPlugins

    @classmethod
    def getPluginAllowedOn(cls, pluginObject):
        """ Utility function that returns a list of event types that this plugin is allowed on.
            If the option was not defined, an empty list is returned
        """
        if pluginObject.hasOption("allowedOn"):
            return pluginObject.getOption("allowedOn").getValue()
        else:
            return []

    @classmethod
    def isAdminOnlyPlugin(cls, plugin):
        """ plugin can be a string with the name of the plugin
            or a Plugin object
        """
        if isinstance(plugin, Plugin):
            pluginId = plugin.getId()
        else:
            pluginId = plugin
        return cls.getCSBookingClass(pluginId)._adminOnly

    @classmethod
    def pluginsWithEventDisplay(cls):
        """ Utility function that returns a list of strings with the names of the
            collaboration plugins that want to display something in event display pages
        """
        l = []
        for pluginName in cls.getCollaborationPluginType().getPlugins():
            if cls.getCSBookingClass(pluginName)._hasEventDisplay:
                l.append(pluginName)
        return l

    @classmethod
    def pluginsWithIndexing(cls, includeNonActive=False):
        """ Utility function that returns a list of strings with the names
            of the collaboration plugins that want to be indexed
        """
        l = []
        for plugin in cls.getCollaborationPluginType().getPlugins(includeNonActive=includeNonActive).values():
            if plugin.getModule().collaboration.CSBooking._shouldBeIndexed:
                l.append(plugin)
        return l

    @classmethod
    def getIndexingFossil(cls, pluginName):
        """ Utility function that returns the fossil that should be used for indexing for a given plugin
        """
        fossilsModule = cls.getModule(pluginName).fossils
        if hasattr(fossilsModule, "ICSBookingIndexingFossil"):
            return fossilsModule.ICSBookingIndexingFossil
        else:
            return ICSBookingBaseIndexingFossil

    @classmethod
    def updateIndexingFossilsDict(cls):
        """ Utility function that updates IQueryResultFossil's getResults method
            with the proper dict in order to fossilize bookings for the VS Overview page
        """
        fossilDict = {"%s.%s" % (Conference.__module__, Conference.__name__): IConferenceFossil,
                      'MaKaC.plugins.Collaboration.indexes.CSBookingInstanceWrapper': ICSBookingInstanceIndexingFossil}
        for pluginName in cls.getCollaborationPluginType().getPlugins(includeNonActive=True):
            classObject = cls.getCSBookingClass(pluginName)
            fossilClassObject = cls.getIndexingFossil(pluginName)
            fossilDict["%s.%s" % (classObject.__module__, classObject.__name__)] = fossilClassObject

        IQueryResultFossil.get('getResults').setTaggedValue('result', fossilDict)

    @classmethod
    def getXMLGenerator(cls, pluginName):
        return cls.getModule(pluginName).pages.XMLGenerator

    @classmethod
    def getServiceInformation(cls, pluginName):
        return cls.getModule(pluginName).pages.ServiceInformation

    @classmethod
    def getRequestTypeUserCanManage(cls, conf, user):
        requestType = ""
        if CollaborationTools.canUserManagePlugin(conf, CollaborationTools.getPlugin("RecordingRequest"), user):
            if CollaborationTools.canUserManagePlugin(conf, CollaborationTools.getPlugin("WebcastRequest"), user):
                requestType = "both"
            else:
                requestType = "recording"
        else:
            if CollaborationTools.canUserManagePlugin(conf, CollaborationTools.getPlugin("WebcastRequest"), user):
                requestType = "webcast"

        return requestType

    """ The CSBooking object which can be passed through to the fossil
        may be linked to a Contribution, in the case of WebcastRequest etc,
        therefore the URL may be more specific than the event in this instance.
    """

    @classmethod
    def getConferenceOrContributionURL(cls, event):
        from MaKaC.webinterface.urlHandlers import UHConferenceDisplay, UHContributionDisplay
        url = ""

        # Webcast and Recording Request specific:
        if hasattr(event, '_conf'):
            event = event._conf

        if isinstance(event, Conference):
            url = UHConferenceDisplay.getURL(event)
        elif isinstance(event, Contribution):
            url = UHContributionDisplay(event)

        return url

    @classmethod
    def getBookingTitle(cls, booking):
        title = None
        parsingAttrs = ['getFullTitle', 'getTitle', '_getTitle']

        for funcName in parsingAttrs:
            if hasattr(booking, funcName):
                func = getattr(booking, funcName)
                title = func()

                if title is not None:
                    break

        if title is None and hasattr(booking, '_conf'):
            title = booking._conf.getTitle()

        return title if title is not None else 'No title defined.'

    @classmethod
    def getBookingShortStatus(cls, booking):
        if booking.hasAcceptReject():
            if booking.getAcceptRejectStatus() is None:
                return 'P'
            else:
                return 'A'
        else:
            return ''

    @classmethod
    def getAudience(cls, booking):
        audience = None

        if booking.getBookingParams().has_key("audience"):
            audience = booking.getBookingParams().get("audience")
            if audience == "":
                audience = "No restriction"
        return audience

    @classmethod
    def getCommonTalkInformation(cls, conference, plugin_name, plugin_option):
        """
        Returns a tuple of 3 lists:
        - List of talks (Contribution objects which are not in a Poster session)
        - List of webcast capable rooms, as a list of "locationName:roomName" strings
        - List of webcast-able talks (list of Contribution objects who take place in a webcast capable room)
        - List of not webcast-able talks (list of Contribution objects who do not take place in a webcast capable room)
        """

        #a talk is defined as a non-poster contribution
        filter = PosterFilterField(conference, False, False)
        talks = [cont for cont in conference.getContributionList() if filter.satisfies(cont)]

        #list of "locationName:roomName" strings
        capableRooms = CollaborationTools.getOptionValueRooms(plugin_name, plugin_option)

        roomFullNames = [r.locationName + ':' + r.getFullName() for r in capableRooms]
        roomNames = [r.locationName + ':' + r.name for r in capableRooms]

        #a webcast-able talk is defined as a talk talking place in a webcast-able room
        ableTalks = []
        unableTalks = []
        for t in talks:
            location = t.getLocation()
            room = t.getRoom()
            if location and room and (location.getName() + ":" + room.getName() in roomNames) and t.isScheduled():
                ableTalks.append(t)
            else:
                unableTalks.append(t)

        return (talks, roomFullNames, roomNames, ableTalks, unableTalks)

    @classmethod
    def isAbleToBeWebcastOrRecorded(cls, obj, plugin_name):
        plugin_option ='recordingCapableRooms' if plugin_name == 'RecordingRequest' else 'webcastCapableRooms'
        capableRooms = CollaborationTools.getOptionValueRooms(plugin_name, plugin_option)
        roomNames = [r.locationName + ':' + r.name for r in capableRooms]
        location = obj.getLocation()
        room = obj.getRoom()
        isAble = location is not None and room is not None and (location.getName() + ":" + room.getName() in roomNames)
        if isinstance(obj, Contribution):
            isAble = isAble and obj.isScheduled()
        return isAble

    @classmethod
    def getCollaborationParams(cls, conf):
        params = {}
        csbm = Catalog.getIdx("cs_bookingmanager_conference").get(conf.getId())
        pluginNames = csbm.getEventDisplayPlugins()
        bookingData = {}
        for pluginName in pluginNames:
            bookingData[pluginName] = CollaborationTools.getServiceInformation(pluginName)
        bookings = csbm.getBookingList(filterByType=pluginNames, notify=True, onlyPublic=True)
        bookings.sort(key=lambda b: b.getStartDate() or minDatetime())
        params['bookings'] = bookings
        params['bookingData'] = bookingData
        return params


class MailTools(object):

    @classmethod
    def getServerName(cls):
        return str(Config.getInstance().getBaseURL())

    @classmethod
    def needToSendEmails(cls, pluginName = None):
        """
        Checks the plugin/global options in order to know if notification e-mails
        need to be sent
        """

        # this is not cool... the object should be passed in the first place
        if pluginName:
            plugin = CollaborationTools.getCollaborationPluginType().getPlugin(pluginName)
        else:
            plugin = None

        if plugin and plugin.hasOption('sendMailNotifications'):
            admins = plugin.getOption('admins').getValue()
            sendMail = plugin.getOption('sendMailNotifications').getValue()
            addEmails = plugin.getOption('additionalEmails').getValue()
        else:
            # get definitions from the Collaboration plugin type
            admins = CollaborationTools.getCollaborationOptionValue('collaborationAdmins')
            sendMail = CollaborationTools.getCollaborationOptionValue('sendMailNotifications')
            addEmails = CollaborationTools.getCollaborationOptionValue('additionalEmails')

        return (sendMail and len(admins) > 0) or len(addEmails) > 0

    @classmethod
    def getAdminEmailList(cls, pluginName = None):
        """ Returns a list of admin email addresses that a notification email should be sent to.
            If pluginName is None, then the global Collaboration admin mails will be returned.
            The emails in the list are not in any particular order and should be unique.
        """

        if pluginName:

            adminEmails = CollaborationTools.getOptionValue(pluginName, 'additionalEmails')
            if CollaborationTools.getOptionValue(pluginName, 'sendMailNotifications'):
                adminEmails.extend([u.getEmail() for u in CollaborationTools.getOptionValue(pluginName, 'admins')])
        else:
            adminEmails = CollaborationTools.getCollaborationOptionValue('additionalEmails')
            if CollaborationTools.getCollaborationOptionValue('sendMailNotifications'):
                adminEmails.extend([u.getEmail() for u in CollaborationTools.getCollaborationOptionValue('collaborationAdmins')])
        return list(set(adminEmails))

    @classmethod
    def getManagersEmailList(cls, conf, pluginName = None):
        """ Returns a list of manager email addresses (for a given event) that a notification email should be sent to.
            This list includes:
                -The creator of an event
                -The managers of an event
                -Any Video Services Managers
                -If pluginName is not None, any Video Services Managers for that given system
            The emails in the list are not in any particular order and should be unique.
        """
        csbm = Catalog.getIdx("cs_bookingmanager_conference").get(conf.getId())
        managersEmails = []
        managersEmails.append(conf.getCreator().getEmail())
        managersEmails.extend([u.getEmail() for u in conf.getManagerList()])
        managersEmails.extend([u.getEmail() for u in csbm.getVideoServicesManagers()])
        if pluginName:
            managersEmails.extend([u.getEmail() for u in csbm.getPluginManagers(pluginName)])
        return list(set(managersEmails))

    @classmethod
    def eventDetails(cls, conf):
        return """
Event details:
<table style="border-spacing: 10px 10px;">
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Event name:</strong>
        </td>
        <td>
            <a href="%s">%s</a>
        </td
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Event dates:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Event id</strong>
        </td>
        <td>
            %s
        </td
    </tr>
    %s
</table>
"""%(urlHandlers.UHConferenceDisplay.getURL(conf),
     conf.getTitle(),
     formatTwoDates(conf.getStartDate(), conf.getEndDate(), tz = conf.getTimezone(), showWeek = True),
     conf.getId(),
     MailTools.eventRoomDetails(conf)
     )


    @classmethod
    def eventRoomDetails(cls, conf):
        location = conf.getLocation()
        room = conf.getRoom()
        if location and location.getName() and location.getName().strip():
            locationText = location.getName().strip()
            if room and room.getName() and room.getName().strip():
                locationText += ". Room: " + room.getName().strip()
            else:
                locationText += " (room not defined)"
        else:
            locationText = "location/room not defined"

        return """
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Event location & room:</strong>
        </td>
        <td>
            %s
        </td>
    </tr>
""" % locationText


    @classmethod
    def userDetails(cls, caption, user):
        additionalEmailsText = ""
        additionalEmails = user.getSecondaryEmails()
        if additionalEmails:
            additionalEmailsText="""
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Additional emails:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
""" % ", ".join(user.getEmails()[1:])

        additionalTelephonesText = ""
        additionalTelephones = user.getSecondaryTelephones()
        if additionalTelephones:
            additionalTelephonesText="""
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Additional telephones:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
""" % ", ".join(user.getTelephone()[1:])


        return """
%s details:
<table style="border-spacing: 10px 10px;">
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Full name:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Main email address:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
    %s
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Main phone number:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
    %s
</table>
""" % (caption,
       user.getFullName(),
       user.getEmail(),
       additionalEmailsText,
       user.getTelephone(),
       additionalTelephonesText
       )

    @classmethod
    def organizerDetails(cls, conf):
        return cls.userDetails('Creator of the event', conf.getCreator())

    @classmethod
    def currentUserDetails(cls, caption):
        if not 'currentUser' in ContextManager.get():
            return ""
        user = ContextManager.get('currentUser')
        return cls.userDetails(caption, user)

    @classmethod
    def bookingCreationDate(cls, booking):
        return formatDateTime(getAdjustedDate(booking.getCreationDate(), booking.getConference()))

    @classmethod
    def bookingModificationDate(cls, booking, typeOfMail):
        if (typeOfMail == 'new'):
            return ""
        else:
            return """
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Modification date:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
""" % formatDateTime(getAdjustedDate(booking.getModificationDate(), booking.getConference()))

    @classmethod
    def talkListText(cls, conf, talkList):
        text = []

        #we sort by start date
        talkList.sort(key = Contribution.contributionStartDateForSort)

        #we check is event is single day
        singleDayEvent = isSameDay(conf.getStartDate(), conf.getEndDate(), conf.getTimezone())

        for contribution in talkList:

            #1. speakers text
            speakerList = contribution.getSpeakerList()
            if speakerList:
                speakers = ', by ' + ", ".join([person.getFullName() for person in speakerList])
            else:
                speakers = ''

            #2. room and location text
            locationStr = MailTools.locationOrRoomToStr(contribution.getLocation())
            roomStr = MailTools.locationOrRoomToStr(contribution.getRoom())
            confLocationStr = MailTools.locationOrRoomToStr(conf.getLocation())
            confRoomStr = MailTools.locationOrRoomToStr(conf.getRoom())

            if locationStr == confLocationStr and roomStr == confRoomStr:
                locationText = ''
            else:
                if locationStr:
                    locationText = "Location: " + locationStr
                    if roomStr:
                        locationText += ', Room: ' + roomStr
                    else:
                        locationText += ', Room: not defined'
                else:
                    locationText = "Location: not defined"

                locationText = " (%s)" % locationText

            #3. dates text
            if not contribution.getStartDate():
                datesText = '(Not scheduled)'
            elif singleDayEvent and isSameDay(conf.getStartDate(), contribution.getStartDate(), conf.getTimezone()):
                datesText = formatTime(contribution.getAdjustedStartDate().time()) + ' (' + formatDuration(contribution.getDuration(), "hours_minutes") + ')'
            else:
                datesText = formatDateTime(contribution.getAdjustedStartDate(), showWeek = True) + ' (' + formatDuration(contribution.getDuration(), "hours_minutes") + ')'

            #4. returned result
            contributionLine = """•%s : <a href="%s">%s</a>%s (id: %s)%s""" % (
                datesText,
                urlHandlers.UHContributionDisplay.getURL(contribution),
                contribution.getTitle(),
                speakers,
                contribution.getId(),
                locationText
            )
            text.append(contributionLine)

        return text

    @classmethod
    def locationOrRoomToStr(cls, object):
        """ Turns a CustomLocation or CustomRoom object into a string,
            testing if the object is None, object.getName() is None.
        """
        if object is None:
            return ''
        elif object.getName() is None:
            return ''
        else:
            return object.getName().strip()

    @classmethod
    def listToStr(cls, list):
        return "<br />".join([("•" + item) for item in list])
