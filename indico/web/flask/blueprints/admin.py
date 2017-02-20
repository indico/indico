# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
from MaKaC.webinterface.rh import admins, maintenance, templates, conferenceModif


admin = IndicoBlueprint('admin', __name__, url_prefix='/admin')

# System settings
admin.add_url_rule('/settings/system', 'adminSystem', admins.RHSystem)
admin.add_url_rule('/settings/system/modify', 'adminSystem-modify', admins.RHSystemModify, methods=('GET', 'POST'))

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

# Layout
admin.add_url_rule('/layout/', 'adminLayout', admins.RHAdminLayoutGeneral, methods=('GET', 'POST'))
admin.add_url_rule('/layout/template-set', 'adminLayout-saveTemplateSet', admins.RHAdminLayoutSaveTemplateSet,
                   methods=('POST',))
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
