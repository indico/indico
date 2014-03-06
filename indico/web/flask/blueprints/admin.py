# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.web.flask.wrappers import IndicoBlueprint
from MaKaC.webinterface.rh import (admins, announcement, maintenance, domains, templates, conferenceModif, services,
                                   wizard)


admin = IndicoBlueprint('admin', __name__, url_prefix='/admin')

# General settings
admin.add_url_rule('/', 'adminList', admins.RHAdminArea)
admin.add_url_rule('/settings/general/news', 'adminList-switchNewsActive', admins.RHAdminSwitchNewsActive)
admin.add_url_rule('/settings/general/instance-tracking', 'adminList-toggleInstanceTracking',
                   admins.RHAdminToggleInstanceTracking)
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

# Wizard
admin.add_url_rule('/wizard', 'wizard', wizard.RHWizard, methods=('GET', 'POST'))
