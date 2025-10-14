# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools
from operator import attrgetter


def get_flat_section_positions_setup_data(regform):
    section_data = {s.id: s.position for s in regform.sections if not s.is_deleted}
    item_data = {f.id: f.position for f in regform.form_items
                 if not f.is_section and not f.is_deleted and not f.parent.is_deleted}
    return {'sections': section_data, 'items': item_data}


def update_regform_item_positions(regform):
    """Update positions when deleting/disabling an item in order to prevent gaps."""
    section_positions = itertools.count(1)
    disabled_section_positions = itertools.count(1000)
    for section in sorted(regform.sections, key=attrgetter('position')):
        section_active = section.is_enabled and not section.is_deleted
        section.position = next(section_positions if section_active else disabled_section_positions)
        # ensure consistent field ordering
        positions = itertools.count(1)
        disabled_positions = itertools.count(1000)
        for child in section.children:
            child_active = child.is_enabled and not child.is_deleted
            child.position = next(positions if child_active else disabled_positions)
