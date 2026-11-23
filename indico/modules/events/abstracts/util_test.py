# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.abstracts.util import filter_field_values
from indico.modules.events.contributions.models.fields import (ContributionField, ContributionFieldValue,
                                                               ContributionFieldVisibility)


@pytest.mark.parametrize(('can_manage', 'owns_abstract', 'expected'), (
    (True, False, ['public', 'submitters', 'managers']),
    (False, True, ['public', 'submitters']),
    (False, False, ['public']),
))
def test_filter_field_values(db, dummy_contribution, can_manage, owns_abstract, expected):
    # positions deliberately differ from the creation order
    fields = [
        ('managers', 3, ContributionFieldVisibility.managers_only, True),
        ('public', 1, ContributionFieldVisibility.public, True),
        ('inactive', 0, ContributionFieldVisibility.public, False),
        ('submitters', 2, ContributionFieldVisibility.managers_and_submitters, True),
    ]
    values = {}
    for title, position, visibility, is_active in fields:
        field = ContributionField(event=dummy_contribution.event, title=title, field_type='text', position=position,
                                  visibility=visibility, is_active=is_active)
        values[title] = ContributionFieldValue(contribution=dummy_contribution, contribution_field=field, data=title)
    db.session.flush()

    field_values = filter_field_values(dummy_contribution.field_values, can_manage, owns_abstract)
    assert field_values == [values[title] for title in expected]
