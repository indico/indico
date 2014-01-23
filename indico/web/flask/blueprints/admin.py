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
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import admins, announcement, taskManager, maintenance, domains, users, groups, templates, \
    conferenceModif, services, api, oauth
from indico.web.flask.wrappers import IndicoBlueprint


admin = IndicoBlueprint('admin', __name__, url_prefix='/admin')

# General settings
admin.add_url_rule('/', 'adminList', admins.RHAdminArea)
admin.add_url_rule('/settings/general/debug', 'adminList-switchDebugActive', admins.RHAdminSwitchDebugActive)
admin.add_url_rule('/settings/general/news', 'adminList-switchNewsActive', admins.RHAdminSwitchNewsActive)
admin.add_url_rule('/settings/general/', 'generalInfoModification', admins.RHGeneralInfoModification)
admin.add_url_rule('/settings/general/', 'generalInfoModification-update', admins.RHGeneralInfoPerformModification,
                   methods=('POST',))

# System settings
admin.add_url_rule('/settings/system', 'adminSystem', admins.RHSystem)
admin.add_url_rule('/settings/system/modify', 'adminSystem-modify', admins.RHSystemModify, methods=('GET', 'POST'))

# Announcement
admin.add_url_rule('/announcement', 'adminAnnouncement', announcement.RHAnnouncementModif)
admin.add_url_rule('/announcement', 'adminAnnouncement-save', announcement.RHAnnouncementModifSave, methods=('POST',))

# News
admin.add_url_rule('/news', 'updateNews', admins.RHUpdateNews)

# Upcoming events
admin.add_url_rule('/upcoming-events', 'adminUpcomingEvents', admins.RHConfigUpcoming)

# Task manager
admin.add_url_rule('/tasks', 'taskManager', taskManager.RHTaskManager)

# Maintenance
admin.add_url_rule('/maintenance/', 'adminMaintenance', maintenance.RHMaintenance)
admin.add_url_rule('/maintenance/pack-db', 'adminMaintenance-pack', maintenance.RHMaintenancePack,
                   methods=('GET', 'POST'))
admin.add_url_rule('/maintenance/pack-db/execute', 'adminMaintenance-performPack', maintenance.RHMaintenancePerformPack,
                   methods=('POST',))
admin.add_url_rule('/maintenance/clean-tmp', 'adminMaintenance-tmpCleanup', maintenance.RHMaintenanceTmpCleanup,
                   methods=('GET', 'POST'))
admin.add_url_rule('/maintenance/clean-tmp/execute', 'adminMaintenance-performTmpCleanup',
                   maintenance.RHMaintenancePerformTmpCleanup, methods=('POST',))

# Protection
admin.add_url_rule('/protection/messages', 'adminProtection', admins.RHAdminProtection)

# IP domains (let's call them "networks" in the URL - that's more fitting)
admin.add_url_rule('/networks/create', 'domainCreation', domains.RHDomainCreation)
admin.add_url_rule('/networks/create', 'domainCreation-create', domains.RHDomainPerformCreation, methods=('POST',))
admin.add_url_rule('/networks/<domainId>/modify', 'domainDataModification', domains.RHDomainModification)
admin.add_url_rule('/networks/<domainId>/modify', 'domainDataModification-modify', domains.RHDomainPerformModification,
                   methods=('POST',))
admin.add_url_rule('/networks/<domainId>/details', 'domainDetails', domains.RHDomainDetails)
admin.add_url_rule('/networks/', 'domainList', domains.RHDomains, methods=('GET', 'POST'))

# Users
admin.add_url_rule('/settings/users/', 'userManagement', users.RHUserManagement)
admin.add_url_rule('/settings/users/creation', 'userManagement-switchAuthorisedAccountCreation',
                   users.RHUserManagementSwitchAuthorisedAccountCreation)
admin.add_url_rule('/settings/users/moderate-creation', 'userManagement-switchModerateAccountCreation',
                   users.RHUserManagementSwitchModerateAccountCreation)
admin.add_url_rule('/settings/users/notify-creation', 'userManagement-switchNotifyAccountCreation',
                   users.RHUserManagementSwitchNotifyAccountCreation)
admin.add_url_rule('/users/', 'userList', users.RHUsers, methods=('GET', 'POST'))
admin.add_url_rule('/users/merge', 'userMerge', admins.RHUserMerge, methods=('GET', 'POST'))

# Groups
admin.add_url_rule('/users/groups/', 'groupList', groups.RHGroups, methods=('GET', 'POST'))
admin.add_url_rule('/users/groups/<groupId>', 'groupDetails', groups.RHGroupDetails)
admin.add_url_rule('/users/groups/<groupId>/modify', 'groupModification', groups.RHGroupModification)
admin.add_url_rule('/users/groups/<groupId>/modify', 'groupModification-update', groups.RHGroupPerformModification,
                   methods=('POST',))
admin.add_url_rule('/users/groups/create', 'groupRegistration', groups.RHGroupCreation)
admin.add_url_rule('/users/groups/create', 'groupRegistration-update', groups.RHGroupPerformCreation, methods=('POST',))

# Layout
admin.add_url_rule('/layout/', 'adminLayout', admins.RHAdminLayoutGeneral, methods=('GET', 'POST'))
admin.add_url_rule('/layout/social', 'adminLayout-saveSocial', admins.RHAdminLayoutSaveSocial, methods=('POST',))
admin.add_url_rule('/layout/template-set', 'adminLayout-saveTemplateSet', admins.RHAdminLayoutSaveTemplateSet,
                   methods=('POST',))
admin.add_url_rule('/layout/styles/timetable/', 'adminLayout-styles', admins.RHStyles, methods=('GET', 'POST'))
admin.add_url_rule('/layout/styles/timetable/create', 'adminLayout-addStyle', admins.RHAddStyle,
                   methods=('GET', 'POST'))
admin.add_url_rule('/layout/styles/timetable/<templatefile>/delete', 'adminLayout-deleteStyle', admins.RHDeleteStyle)
admin.add_url_rule('/layout/styles/conference/', 'adminConferenceStyles', admins.RHConferenceStyles)

# Badge templates
admin.add_url_rule('/layout/badges/', 'badgeTemplates', templates.RHBadgeTemplates, methods=('GET', 'POST'))
admin.add_url_rule('/layout/badges/save', 'badgeTemplates-badgePrinting', conferenceModif.RHConfBadgePrinting,
                   methods=('GET', 'POST'))
admin.add_url_rule('/layout/badges/pdf-options', 'adminLayout-setDefaultPDFOptions', templates.RHSetDefaultPDFOptions,
                   methods=('POST',))
admin.add_url_rule('/layout/badges/design', 'badgeTemplates-badgeDesign', templates.RHConfBadgeDesign,
                   methods=('GET', 'POST'))

# Poster templates
admin.add_url_rule('/layout/posters/', 'posterTemplates', templates.RHPosterTemplates, methods=('GET', 'POST'))
admin.add_url_rule('/layout/posters/save', 'posterTemplates-posterPrinting', conferenceModif.RHConfPosterPrinting,
                   methods=('GET', 'POST'))
admin.add_url_rule('/layout/posters/design', 'posterTemplates-posterDesign', templates.RHConfPosterDesign,
                   methods=('GET', 'POST'))

# IP ACL
admin.add_url_rule('/protection/ip-acl', 'adminServices-ipbasedacl', services.RHIPBasedACL)
admin.add_url_rule('/protection/ip-acl/add', 'adminServices-ipbasedacl_fagrant', services.RHIPBasedACLFullAccessGrant,
                   methods=('POST',))
admin.add_url_rule('/protection/ip-acl/remove', 'adminServices-ipbasedacl_farevoke',
                   services.RHIPBasedACLFullAccessRevoke, methods=('POST',))

# HTTP API
admin.add_url_rule('/api/', 'adminServices-apiOptions', api.RHAdminAPIOptions)
admin.add_url_rule('/api/', 'adminServices-apiOptionsSet', api.RHAdminAPIOptionsSet, methods=('POST',))
admin.add_url_rule('/api/keys', 'adminServices-apiKeys', api.RHAdminAPIKeys)

# OAuth
admin.add_url_rule('/oauth/consumers', 'adminServices-oauthAuthorized', oauth.RHAdminOAuthAuthorized)
admin.add_url_rule('/oauth/authorized', 'adminServices-oauthConsumers', oauth.RHAdminOAuthConsumers)

# Analytics
admin.add_url_rule('/analytics', 'adminServices-analytics', services.RHAnalytics)
admin.add_url_rule('/analytics', 'adminServices-saveAnalytics', services.RHSaveAnalytics, methods=('POST',))

# Webcast
admin.add_url_rule('/webcast/live', 'adminServices-webcast', services.RHWebcast, methods=('GET', 'POST'))
admin.add_url_rule('/webcast/setup/', 'adminServices-webcastSetup', services.RHWebcastSetup)
admin.add_url_rule('/webcast/setup/sync/set-url', 'adminServices-webcastSaveWebcastSynchronizationURL',
                   services.RHWebcastSaveWebcastSynchronizationURL, methods=('POST',))
admin.add_url_rule('/webcast/setup/sync', 'adminServices-webcastManualSynchronization',
                   services.RHWebcastManuelSynchronizationURL, methods=('POST',))
admin.add_url_rule('/webcast/setup/stream/add', 'adminServices-webcastAddStream', services.RHWebcastAddStream,
                   methods=('POST',))
admin.add_url_rule('/webcast/setup/stream/remove', 'adminServices-webcastRemoveStream', services.RHWebcastRemoveStream)
admin.add_url_rule('/webcast/setup/channel/move/down', 'adminServices-webcastMoveChannelDown',
                   services.RHWebcastMoveChannelDown)
admin.add_url_rule('/webcast/setup/channel/move/up', 'adminServices-webcastMoveChannelUp',
                   services.RHWebcastMoveChannelUp)
admin.add_url_rule('/webcast/setup/channel/remove', 'adminServices-webcastRemoveChannel',
                   services.RHWebcastRemoveChannel)
admin.add_url_rule('/webcast/setup/channel/modify', 'adminServices-webcastModifyChannel',
                   services.RHWebcastModifyChannel, methods=('POST',))
admin.add_url_rule('/webcast/setup/channel/add', 'adminServices-webcastAddChannel', services.RHWebcastAddChannel,
                   methods=('POST',))
admin.add_url_rule('/webcast/archive/', 'adminServices-webcastArchive', services.RHWebcastArchive)
admin.add_url_rule('/webcast/<webcastid>/archive', 'adminServices-webcastArchiveWebcast',
                   services.RHWebcastArchiveWebcast)
admin.add_url_rule('/webcast/<webcastid>/unarchive', 'adminServices-webcastUnArchiveWebcast',
                   services.RHWebcastUnArchiveWebcast)
admin.add_url_rule('/webcast/<webcastid>/remove', 'adminServices-webcastRemoveWebcast', services.RHWebcastRemoveWebcast)
admin.add_url_rule('/webcast/add', 'adminServices-webcastAddWebcast', services.RHWebcastAddWebcast, methods=('POST',))
admin.add_url_rule('/webcast/onair/add', 'adminServices-webcastAddOnAir', services.RHWebcastAddOnAir)
admin.add_url_rule('/webcast/onair/remove', 'adminServices-webcastRemoveFromAir', services.RHWebcastRemoveFromAir)
admin.add_url_rule('/webcast/channel/switch', 'adminServices-webcastSwitchChannel', services.RHWebcastSwitchChannel)

# Plugins
admin.add_url_rule('/plugins/', 'adminPlugins', admins.RHAdminPlugins, methods=('GET', 'POST'))
admin.add_url_rule('/settings/plugins/reload-all', 'adminPlugins-saveOptionReloadAll',
                   admins.RHAdminPluginsSaveOptionReloadAll, methods=('POST',))
admin.add_url_rule('/plugins/reload-all', 'adminPlugins-reloadAll', admins.RHAdminPluginsReloadAll, methods=('POST',))
admin.add_url_rule('/plugins/clear-all-info', 'adminPlugins-clearAllInfo', admins.RHAdminPluginsClearAllInfo,
                   methods=('POST',))
admin.add_url_rule('/plugins/type/<pluginType>/', 'adminPlugins', admins.RHAdminPlugins, methods=('GET', 'POST'))
admin.add_url_rule('/plugins/type/<pluginType>/reload', 'adminPlugins-reload', admins.RHAdminPluginsReload,
                   methods=('POST',))
admin.add_url_rule('/plugins/type/<pluginType>/toggle', 'adminPlugins-toggleActivePluginType',
                   admins.RHAdminTogglePluginType)
admin.add_url_rule('/plugins/type/<pluginType>/save-options', 'adminPlugins-savePluginTypeOptions',
                   admins.RHAdminPluginsSaveTypeOptions, methods=('POST',))
admin.add_url_rule('/plugins/plugin/<pluginType>/<pluginId>/toggle', 'adminPlugins-toggleActive',
                   admins.RHAdminTogglePlugin)
admin.add_url_rule('/plugins/plugin/<pluginType>/<pluginId>/save-options', 'adminPlugins-savePluginOptions',
                   admins.RHAdminPluginsSaveOptions, methods=('POST',))
