# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.categories.models.categories import Category
from indico.modules.designer import TemplateType
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.pdf import PIXELS_CM
from indico.modules.designer.placeholders import GROUPS
from indico.modules.events.models.events import Event
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.util.date_time import now_utc
from indico.util.placeholders import get_placeholders


FORMAT_MAP_PORTRAIT = {
    'A0': (84.1, 118.9),
    'A1': (59.4, 84.1),
    'A2': (42.0, 59.4),
    'A3': (29.7, 42.0),
    'A4': (21.0, 29.7),
    'A5': (14.8, 21.0),
    'A6': (10.5, 14.8),
    'A7': (7.4, 10.5),
    'A8': (5.2, 7.4),
}


def get_placeholder_options(regform=None):
    return {name: placeholder
            for name, placeholder in get_placeholders('designer-fields', regform=regform).items()
            if not placeholder.admin_only or session.user.is_admin}


def get_nested_placeholder_options(regform=None):
    groups = {group_id: group | {'options': {}} for group_id, group in GROUPS.items()}
    for name, placeholder in get_placeholder_options(regform=regform).items():
        groups[placeholder.group]['options'][name] = str(placeholder.description)
    if not groups['regform_fields']['options']:
        # remove empty group from unlinked regform
        del groups['regform_fields']
    return groups


def get_image_placeholder_types(regform=None):
    return [name for name, placeholder in get_placeholder_options(regform).items() if placeholder.is_image]


def is_regform_field_placeholder(designer_item):
    """Return `True` if the given designer item references a regform field placeholder."""
    return designer_item['type'].startswith('field-')


def get_all_templates(obj):
    """Get all templates usable by an event/category."""
    category = (obj.category or Category.get_root()) if isinstance(obj, Event) else obj
    return set(DesignerTemplate.query.filter(DesignerTemplate.category_id.in_(categ['id'] for categ in category.chain)))


def get_inherited_templates(obj):
    """Get all templates inherited by a given event/category."""
    return get_all_templates(obj) - set(obj.designer_templates)


def get_not_deletable_templates(obj):
    """Get all non-deletable templates for an event/category."""
    not_deletable_criteria = [
        DesignerTemplate.is_system_template,
        DesignerTemplate.backside_template_of != None,  # noqa: E711
        DesignerTemplate.ticket_for_regforms.any(RegistrationForm.event.has(Event.ends_after(now_utc())))
    ]
    return set(DesignerTemplate.query.filter(DesignerTemplate.owner == obj, db.or_(*not_deletable_criteria)))


def get_default_ticket_on_category(category, only_inherited=False):
    if category is None:
        category = Category.get_root()
    if not only_inherited and category.default_ticket_template:
        return category.default_ticket_template
    parent_chain = category.parent_chain_query.options(joinedload('default_ticket_template')).all()
    return next((category.default_ticket_template for
                 category in reversed(parent_chain) if category.default_ticket_template), None)


def get_default_badge_on_category(category, only_inherited=False):
    if category is None:
        category = Category.get_root()
    if not only_inherited and category.default_badge_template:
        return category.default_badge_template
    parent_chain = category.parent_chain_query.options(joinedload('default_badge_template')).all()
    return next((category.default_badge_template for
                 category in reversed(parent_chain) if category.default_badge_template), None)


def get_badge_format(tpl):
    if tpl.data['width'] > tpl.data['height']:
        format_map = {name: (h, w) for name, (w, h) in FORMAT_MAP_PORTRAIT.items()}
    else:
        format_map = FORMAT_MAP_PORTRAIT
    return next((frm for frm, frm_size in format_map.items()
                 if (frm_size[0] == float(tpl.data['width']) / PIXELS_CM and
                     frm_size[1] == float(tpl.data['height']) / PIXELS_CM)), 'custom')


def has_regform_field_placeholders(data):
    """Return `True` if the given template data contains regform field placeholders."""
    return any(is_regform_field_placeholder(item) for item in data['items'])


def can_link_to_regform(template, regform):
    """Return True if the given template can be linked to the given registration form."""
    return regform in get_linkable_regforms(template)


def get_linkable_regforms(template):
    """Return all registration forms that can be linked to the given template."""
    if template.category or template.type == TemplateType.poster or template.registration_form:
        return []

    return [
        regform for regform in template.event.registration_forms
        if (  # If the template has a backside, the backside must be linked to the same regform
            template.backside_template is None
            or template.backside_template.registration_form is None
            or regform == template.backside_template.registration_form
        )
        and all(  # If the the template is a backside, all frontsides must be linked to the same regform
            tpl.registration_form is None or tpl.registration_form == regform for tpl in template.backside_template_of
        )
    ]


def get_printable_event_templates(regform):
    """Return all templates that can be used to print badges/tickets for the given registration form.

    A template can be used if it is either not linked to anything or linked to the current registation form.
    """
    return (
        DesignerTemplate.query
        .with_parent(regform.event)
        .filter(db.or_(DesignerTemplate.registration_form_id.is_(None),
                       DesignerTemplate.registration_form == regform))
        .all()
    )
