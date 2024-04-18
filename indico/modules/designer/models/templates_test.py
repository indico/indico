# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

pytest_plugins = ('indico.modules.designer.testing.fixtures',
                  'indico.modules.events.registration.testing.fixtures')


def test_template_is_unlinkable(dummy_designer_template):
    """`template.is_unlinkable` should be `False` if the template contains custom registration placeholders."""
    assert dummy_designer_template.is_unlinkable

    original_data = dummy_designer_template.data
    # Add regform field placeholders to the template
    items = {'items': [*original_data['items'], {'type': 'field-1'}, {'type': 'field-2'}]}
    dummy_designer_template.data |= items

    assert not dummy_designer_template.is_unlinkable
