# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.placeholders import GROUP_TITLES
from indico.modules.events.models.events import Event
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.util.date_time import now_utc
from indico.util.placeholders import get_placeholders


def get_placeholder_options():
    return {name: placeholder
            for name, placeholder in get_placeholders('designer-fields').viewitems()
            if not placeholder.admin_only or session.user.is_admin}


def get_nested_placeholder_options():
    groups = {group_id: {'title': group_title, 'options': {}} for group_id, group_title in GROUP_TITLES.viewitems()}
    for name, placeholder in get_placeholder_options().viewitems():
        groups[placeholder.group]['options'][name] = unicode(placeholder.description)
    return groups


def get_image_placeholder_types():
    return [name for name, placeholder in get_placeholder_options().viewitems() if placeholder.is_image]


def get_all_templates(obj):
    """Get all templates usable by an event/category."""
    category = obj.category if isinstance(obj, Event) else obj
    return set(DesignerTemplate.find_all(DesignerTemplate.category_id.in_(categ['id'] for categ in category.chain)))


def get_inherited_templates(obj):
    """Get all templates inherited by a given event/category."""
    return get_all_templates(obj) - set(obj.designer_templates)


def get_not_deletable_templates(obj):
    """Get all non-deletable templates for an event/category."""
    not_deletable_criteria = [
        DesignerTemplate.is_system_template,
        DesignerTemplate.backside_template_of != None,  # noqa
        DesignerTemplate.ticket_for_regforms.any(RegistrationForm.event.has(Event.ends_after(now_utc())))
    ]
    return set(DesignerTemplate.query.filter(DesignerTemplate.owner == obj, db.or_(*not_deletable_criteria)))


def get_default_ticket_on_category(category, only_inherited=False):
    if not only_inherited and category.default_ticket_template:
        return category.default_ticket_template
    parent_chain = category.parent_chain_query.options(joinedload('default_ticket_template')).all()
    return next((category.default_ticket_template for
                 category in reversed(parent_chain) if category.default_ticket_template), None)


def get_default_badge_on_category(category, only_inherited=False):
    if not only_inherited and category.default_badge_template:
        return category.default_badge_template
    parent_chain = category.parent_chain_query.options(joinedload('default_badge_template')).all()
    return next((category.default_badge_template for
                 category in reversed(parent_chain) if category.default_badge_template), None)
