# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories import Category
from indico.modules.email_templates.models.email_templates import EmailTemplate
from indico.modules.events import Event


def get_all_templates(obj):
    """Get all templates usable by an event/category."""
    category = (obj.category or Category.get_root()) if isinstance(obj, Event) else obj
    return set(EmailTemplate.query.filter(EmailTemplate.category_id.in_(categ['id'] for categ in category.chain)))


def get_inherited_templates(obj):
    """Get all templates inherited by a given event/category."""
    return get_all_templates(obj) - set(obj.email_templates)
