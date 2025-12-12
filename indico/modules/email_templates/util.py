# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy import or_

from indico.modules.categories import Category
from indico.modules.email_templates.models.email_templates import EmailTemplate
from indico.modules.events import Event


def get_all_templates(obj):
    """Get all templates usable by an event/category."""
    if isinstance(obj, Event):
        category = obj.category or Category.get_root()
        return set(
            EmailTemplate.query.filter(
                EmailTemplate.category_id.in_(
                    category['id'] for category in category.chain
                )
            )
        ) | set(obj.email_templates)
    return set(
        EmailTemplate.query.filter(
            EmailTemplate.category_id.in_(
                category['id'] for category in obj.chain
            )
        )
    )


def get_inherited_templates(obj):
    """Get all templates inherited by a given event/category."""
    return get_all_templates(obj) - set(obj.email_templates)


def get_email_template(obj, *, template_type, status=None):
    """
    Return the most specific active email template, or None.

    Specificity order:
    1. Event-specific template
    2. Deeper category in the chain
    """
    if isinstance(obj, Event):
        event = obj
        category = event.category or Category.get_root()
    else:
        event = None
        category = obj
    category_ids = [c['id'] for c in category.chain]
    query = EmailTemplate.query.filter(EmailTemplate.is_active.is_(True), EmailTemplate.type == template_type)
    if event:
        query = query.filter(or_(EmailTemplate.event == event, EmailTemplate.category_id.in_(category_ids)))
    else:
        query = query.filter(EmailTemplate.category_id.in_(category_ids))
    if template_type == 'registration_state_update' and status is not None:
        query = query.filter(EmailTemplate.rules['status'].astext == status)
    return query.order_by(EmailTemplate.event_id.is_(None), EmailTemplate.category_id.desc()).first()
