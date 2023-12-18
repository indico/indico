# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


pytest_plugins = ('indico.modules.designer.testing.fixtures',
                  'indico.modules.events.registration.testing.fixtures')


def test_template_link_to_regform(dummy_event, dummy_regform, create_designer_template):
    """Ensure that a template can be linked and unlinked from a registration form."""
    template = create_designer_template('Event template', event=dummy_event)
    template.link_regform(dummy_regform)

    original_data = template.data
    # Add dynamic items to the template
    template.data = template.data | {'items': [*original_data['items'], {'type': 'dynamic-1'}, {'type': 'dynamic-2'}]}

    template.unlink_regform()
    # Unlinking deletes all dynamic items (since those reference the regform)
    assert template.data == original_data
