# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

pytest_plugins = ('indico.modules.designer.testing.fixtures',
                  'indico.modules.events.registration.testing.fixtures')


def test_template_link_to_regform(dummy_regform, dummy_designer_template):
    """Ensure that a template can be linked and unlinked from a registration form."""
    dummy_designer_template.link_regform(dummy_regform)

    original_data = dummy_designer_template.data
    # Add dynamic items to the template
    items = {'items': [*original_data['items'], {'type': 'dynamic-1'}, {'type': 'dynamic-2'}]}
    dummy_designer_template.data = dummy_designer_template.data | items

    dummy_designer_template.unlink_regform()
    # Unlinking deletes all dynamic items (since those reference the regform)
    assert dummy_designer_template.data == original_data
