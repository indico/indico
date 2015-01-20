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

from MaKaC.webinterface.rh import categoryMod
from indico.web.flask.wrappers import IndicoBlueprint


category_mgmt = IndicoBlueprint('category_mgmt', __name__, url_prefix='/category/<categId>/manage')


# Creation
category_mgmt.add_url_rule('!/category/<categId>/create/subcategory', 'categoryCreation',
                           categoryMod.RHCategoryCreation, methods=('GET', 'POST'))
category_mgmt.add_url_rule('!/category/<categId>/create/subcategory/save', 'categoryCreation-create',
                           categoryMod.RHCategoryPerformCreation, methods=('POST',))
# Event creation is in event.creation

# General settings
category_mgmt.add_url_rule('/', 'categoryModification', categoryMod.RHCategoryModification)
category_mgmt.add_url_rule('/data', 'categoryDataModification', categoryMod.RHCategoryDataModif,
                           methods=('GET', 'POST'))
category_mgmt.add_url_rule('/data/save', 'categoryDataModification-modify', categoryMod.RHCategoryPerformModification,
                           methods=('POST',))
category_mgmt.add_url_rule('/settings/tasks', 'categoryDataModification-tasksOption', categoryMod.RHCategoryTaskOption,
                           methods=('GET', 'POST'))
category_mgmt.add_url_rule('/events', 'categoryModification-actionConferences', categoryMod.RHCategoryActionConferences,
                           methods=('GET', 'POST'))
category_mgmt.add_url_rule('/subcategories', 'categoryModification-actionSubCategs',
                           categoryMod.RHCategoryActionSubCategs, methods=('GET', 'POST'))
# Files
category_mgmt.add_url_rule('/files', 'categoryFiles', categoryMod.RHCategoryFiles)
category_mgmt.add_url_rule('/files/add', 'categoryFiles-addMaterial', categoryMod.RHAddMaterial, methods=('POST',))

# Protection
category_mgmt.add_url_rule('/access', 'categoryAC', categoryMod.RHCategoryAC)
category_mgmt.add_url_rule('/access/visibility', 'categoryAC-setVisibility', categoryMod.RHCategorySetVisibility,
                           methods=('POST',))
category_mgmt.add_url_rule('/access/create-control', 'categoryConfCreationControl-setCreateConferenceControl',
                           categoryMod.RHCategorySetConfControl, methods=('POST',))
category_mgmt.add_url_rule('/access/notify-creation', 'categoryConfCreationControl-setNotifyCreation',
                           categoryMod.RHCategorySetNotifyCreation, methods=('POST',))

# Tools
category_mgmt.add_url_rule('/tools/', 'categoryTools', categoryMod.RHCategoryTools)
category_mgmt.add_url_rule('/tools/delete', 'categoryTools-delete', categoryMod.RHCategoryDeletion, methods=('POST',))

# Tasks (unused, possibly even obsolete)
category_mgmt.add_url_rule('/tasks', 'categoryTasks', categoryMod.RHCategoryTasks, methods=('GET', 'POST'))
category_mgmt.add_url_rule('/tasks/action', 'categoryTasks-taskAction', categoryMod.RHCategoryTasksAction,
                           methods=('GET', 'POST'))
