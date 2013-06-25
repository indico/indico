# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from flask import Blueprint

from MaKaC.webinterface.rh import admins, announcement, taskManager, maintenance, domains, users, groups
from indico.web.flask.util import rh_as_view


admin = Blueprint('admin', __name__, url_prefix='/admin')

# General settings
admin.add_url_rule('/', 'adminList', rh_as_view(admins.RHAdminArea))
admin.add_url_rule('/settings/general/cache', 'adminList-switchCacheActive',
                   rh_as_view(admins.RHAdminSwitchCacheActive))
admin.add_url_rule('/settings/general/debug', 'adminList-switchDebugActive',
                   rh_as_view(admins.RHAdminSwitchDebugActive))
admin.add_url_rule('/settings/general/news', 'adminList-switchNewsActive',
                   rh_as_view(admins.RHAdminSwitchNewsActive))

# System settings
admin.add_url_rule('/settings/system', 'adminSystem', rh_as_view(admins.RHSystem))
admin.add_url_rule('/settings/system/modify', 'adminSystem-modify', rh_as_view(admins.RHSystemModify),
                   methods=('GET', 'POST'))

# Announcement
admin.add_url_rule('/announcement', 'adminAnnouncement', rh_as_view(announcement.RHAnnouncementModif))
admin.add_url_rule('/announcement', 'adminAnnouncement-save', rh_as_view(announcement.RHAnnouncementModifSave),
                   methods=('POST',))

# News
admin.add_url_rule('/news', 'updateNews', rh_as_view(admins.RHUpdateNews))

# Upcoming events
admin.add_url_rule('/upcoming-events', 'adminUpcomingEvents', rh_as_view(admins.RHConfigUpcoming))

# Task manager
admin.add_url_rule('/tasks', 'taskManager', rh_as_view(taskManager.RHTaskManager))

# Maintenance
admin.add_url_rule('/maintenance/', 'adminMaintenance', rh_as_view(maintenance.RHMaintenance))
admin.add_url_rule('/maintenance/pack-db', 'adminMaintenance-pack', rh_as_view(maintenance.RHMaintenancePack),
                   methods=('GET', 'POST'))
admin.add_url_rule('/maintenance/pack-db/execute', 'adminMaintenance-performPack',
                   rh_as_view(maintenance.RHMaintenancePerformPack), methods=('POST',))
admin.add_url_rule('/maintenance/clean-tmp', 'adminMaintenance-tmpCleanup',
                   rh_as_view(maintenance.RHMaintenanceTmpCleanup), methods=('GET', 'POST'))
admin.add_url_rule('/maintenance/clean-tmp/execute', 'adminMaintenance-performTmpCleanup',
                   rh_as_view(maintenance.RHMaintenancePerformTmpCleanup), methods=('POST',))

# Protection
admin.add_url_rule('/protection', 'adminProtection', rh_as_view(admins.RHAdminProtection))

# IP domains (let's call them "networks" in the URL - that's more fitting)
admin.add_url_rule('/networks/create', 'domainCreation', rh_as_view(domains.RHDomainCreation))
admin.add_url_rule('/networks/create', 'domainCreation-create', rh_as_view(domains.RHDomainPerformCreation),
                   methods=('POST',))
admin.add_url_rule('/networks/<domainId>/modify', 'domainDataModification', rh_as_view(domains.RHDomainModification))
admin.add_url_rule('/networks/<domainId>/modify', 'domainDataModification-modify',
                   rh_as_view(domains.RHDomainPerformModification), methods=('POST',))
admin.add_url_rule('/networks/<domainId>/details', 'domainDetails', rh_as_view(domains.RHDomainDetails))
admin.add_url_rule('/networks/', 'domainList', rh_as_view(domains.RHDomains), methods=('GET', 'POST'))

# Users
admin.add_url_rule('/settings/users/', 'userManagement', rh_as_view(users.RHUserManagement))
admin.add_url_rule('/settings/users/creation', 'userManagement-switchAuthorisedAccountCreation',
                   rh_as_view(users.RHUserManagementSwitchAuthorisedAccountCreation))
admin.add_url_rule('/settings/users/moderate-creation', 'userManagement-switchModerateAccountCreation',
                   rh_as_view(users.RHUserManagementSwitchModerateAccountCreation))
admin.add_url_rule('/settings/users/notify-creation', 'userManagement-switchNotifyAccountCreation',
                   rh_as_view(users.RHUserManagementSwitchNotifyAccountCreation))
admin.add_url_rule('/users/', 'userList', rh_as_view(users.RHUsers), methods=('GET', 'POST'))

# Groups
admin.add_url_rule('/users/groups/', 'groupList', rh_as_view(groups.RHGroups), methods=('GET', 'POST'))
admin.add_url_rule('/users/groups/<groupId>', 'groupDetails', rh_as_view(groups.RHGroupDetails))
admin.add_url_rule('/users/groups/<groupId>/modify', 'groupModification', rh_as_view(groups.RHGroupModification))
admin.add_url_rule('/users/groups/<groupId>/modify', 'groupModification-update',
                   rh_as_view(groups.RHGroupPerformModification), methods=('POST',))
admin.add_url_rule('/users/groups/create', 'groupRegistration', rh_as_view(groups.RHGroupCreation))
admin.add_url_rule('/users/groups/create', 'groupRegistration-update',
                   rh_as_view(groups.RHGroupPerformCreation), methods=('POST',))
