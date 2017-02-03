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

from __future__ import unicode_literals

from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.placeholders import GROUP_TITLES
from indico.modules.events.models.events import Event
from indico.util.placeholders import get_placeholders


def get_placeholder_options():
    groups = {group_id: {'title': group_title, 'options': {}} for group_id, group_title in GROUP_TITLES.viewitems()}
    for pname, placeholder in get_placeholders('designer-fields').viewitems():
        groups[placeholder.group]['options'][pname] = placeholder.description
    return groups


def get_all_templates(obj):
    """Get all templates usable by an event/category"""
    category = obj.category if isinstance(obj, Event) else obj
    return set(DesignerTemplate.find_all(DesignerTemplate.category_id.in_(categ['id'] for categ in category.chain)))


def get_inherited_templates(obj):
    """Get all templates inherited by a given event/category"""
    return get_all_templates(obj) - set(obj.designer_templates)
