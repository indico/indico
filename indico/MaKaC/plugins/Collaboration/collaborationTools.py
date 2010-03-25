# -*- coding: utf-8 -*-
##
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

from MaKaC.plugins.base import PluginsHolder, Plugin
from MaKaC.webinterface import urlHandlers
from MaKaC.common.utils import formatDateTime, formatTwoDates, formatTime,\
    formatDuration
from MaKaC.common.timezoneUtils import getAdjustedDate, isSameDay
from MaKaC.common.Configuration import Config
from MaKaC.conference import Contribution

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
    def getPlugin(cls, pluginName):
        #This commented code tried to gain some performance by caching the collaboration
        # PluginType object, but sometimes there would be problems by
        # different requests sharing memory and trying to access the database
        # after a connection was closed. This happened under Apache in Windows Vista with ZODB 3.8

#        if not pluginName in cls._plugins:
#            cls._plugins[pluginName] = cls.getCollaborationPluginType().getPlugin(pluginName)
#        return cls._plugins[pluginName]
        return cls.getCollaborationPluginType().getPlugin(pluginName)

    @classmethod
    def anyPluginsAreActive(cls):
        return len(cls.getCollaborationPluginType().getPlugins(includeNonActive = False)) > 0

    @classmethod
    def getOptionValue(cls, pluginName, optionName):
        """ Returns the value of an option of a plugin (plugins/Collaboration/XXXXX/options.py)
            pluginName: a string with the name of the plugin
            optionName: a string with the name of the option
        """
        ph = PluginsHolder()
        return ph.getPluginType("Collaboration").getPlugin(pluginName).getOption(optionName).getValue()

    @classmethod
    def getCollaborationOptionValue(cls, optionName):
        """ Returns the value of an option of the Collaboration plugin type (plugins/Collaboration/options.py)
        """
        return cls.getCollaborationPluginType().getOption(optionName).getValue()

    @classmethod
    def isUsingHTTPS(cls):
        """ Utility function that returns if we should use HTTPS in collaboration pages or not.
        """
        return cls.getCollaborationPluginType().hasOption('useHTTPS') and \
               cls.getCollaborationPluginType().getOption('useHTTPS').getValue()

    @classmethod
    def getModule(cls, pluginName):
        """ Utility function that returns a module object given a plugin name.
            pluginName: a string such as "EVO", "DummyPlugin", etc.
        """
        return cls.getCollaborationPluginType().getPlugin(pluginName).getModule()

    @classmethod
    def getTemplateClass(cls, pluginName, templateName):
        """ Utility function that returns a template class object given a plugin name and the class name.
            Example: templateClass = CollaborationTools.getTemplateClass("EVO", "WNewBookingForm") will return the WNewBookingForm class in the EVO plugin.
        """
        return cls.getModule(pluginName).pages.__dict__.get(templateName, None)

    @classmethod
    def getServiceClass(cls, pluginName, serviceName):
        """ Utility function that returns a service class object given a plugin name and the class name.
            Example: serviceClass = CollaborationTools.getTemplateClass("WebcastRequest", "WebcastAbleTalksService") will return the WebcastAbleTalksService class in the WebcastRequest plugin.
        """
        return cls.getModule(pluginName).services.__dict__.get(serviceName + "Service", None)

    @classmethod
    def getExtraCSS(cls, pluginName):
        """ Utility function that returns a string with the extra CSS declared by a plugin.
            Example: templateClass = CollaborationTools.getExtraCSS("EVO").
        """
        templateClass = cls.getTemplateClass(pluginName, "WStyle")
        if templateClass:
            return templateClass(pluginName).getHTML()
        else:
            return None

    @classmethod
    def getExtraJS(cls, conf, pluginName, user):
        """ Utility function that returns a string with the extra JS declared by a plugin.
        """
        templateClass = cls.getTemplateClass(pluginName, "WExtra")
        if templateClass:
            return templateClass(conf, pluginName, user).getHTML()
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
        csbm = conference.getCSBookingManager()

        # we get the list of Plugin objects allowed for this kind of event
        allowedForThisEvent = csbm.getAllowedPlugins()

        for plugin in allowedForThisEvent:

            if cls.canUserManagePlugin(conference, plugin, user):

                tabNamesSet.add(cls.getPluginTab(plugin))


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

            csbm = conference.getCSBookingManager()

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
        csbm = conference.getCSBookingManager()

        from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin
        isAdminUser = RCCollaborationAdmin.hasRights(user = user)

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
        singleBookingPlugins = [p for p in pluginList if not cls.getCSBookingClass(p.getName())._allowMultiple]
        multipleBookingPlugins = [p for p in pluginList if cls.getCSBookingClass(p.getName())._allowMultiple]

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
            pluginName = plugin.getName()
        else:
            pluginName = plugin
        return cls.getCSBookingClass(pluginName)._adminOnly

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
    def pluginsWithIndexing(cls):
        """ Utility function that returns a list of strings with the names
            of the collaboration plugins that want to be indexed
        """
        l = []
        for pluginName in cls.getCollaborationPluginType().getPlugins():
            if cls.getCSBookingClass(pluginName)._shouldBeIndexed:
                l.append(pluginName)
        return l

    @classmethod
    def getXMLGenerator(cls, pluginName):
        return cls.getModule(pluginName).pages.XMLGenerator


class MailTools(object):

    @classmethod
    def getServerName(cls):
        return str(Config.getInstance().getBaseURL())

    @classmethod
    def needToSendEmails(cls, pluginName = None):
        if pluginName:
            admins = CollaborationTools.getOptionValue(pluginName, 'admins')
            sendMailNotifications = CollaborationTools.getOptionValue(pluginName, 'sendMailNotifications')
            additionalEmails = CollaborationTools.getOptionValue(pluginName, 'additionalEmails')
        else:
            admins = CollaborationTools.getCollaborationOptionValue('collaborationAdmins')
            sendMailNotifications = CollaborationTools.getCollaborationOptionValue('sendMailNotifications')
            additionalEmails = CollaborationTools.getCollaborationOptionValue('additionalEmails')

        return (sendMailNotifications and len(admins) > 0) or len(additionalEmails) > 0

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
        csbm = conf.getCSBookingManager()
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
        roomDetails = ""
        location = conf.getLocation()
        if location:
            roomDetails += """
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Event location:</strong>
        </td>
        <td>
            %s
        </td>
    </tr>
""" % location.getName()

            room = conf.getRoom()
            if room:
                roomDetails += """
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Event room:</strong>
        </td>
        <td>
            %s
        </td>
    </tr>
""" % room.getName()

        return roomDetails


    @classmethod
    def organizerDetails(cls, conf):
        creator = conf.getCreator()

        additionalEmailsText = ""
        additionalEmails = creator.getSecondaryEmails()
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
""" % ", ".join(creator.getEmails()[1:])

        additionalTelephonesText = ""
        additionalTelephones = creator.getSecondaryTelephones()
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
""" % ", ".join(creator.getTelephone()[1:])


        return """
Creator of the event details:
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
""" % (creator.getFullName(),
       creator.getEmail(),
       additionalEmailsText,
       creator.getTelephone(),
       additionalTelephonesText
       )

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
