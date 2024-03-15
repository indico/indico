# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.designer import TemplateType
from indico.modules.designer.util import can_link_to_regform, get_printable_event_templates


pytest_plugins = ('indico.modules.designer.testing.fixtures',
                  'indico.modules.events.registration.testing.fixtures')


def test_get_printable_event_templates(dummy_category, dummy_event, create_regform, create_dummy_designer_template):
    """
    Ensure that all templates that are available for printing for a given regform are
    either linked to the regform or not linked to any.
    """
    create_dummy_designer_template('Category template', category=dummy_category)
    event_template_1 = create_dummy_designer_template('Event template 1', event=dummy_event)
    event_template_2 = create_dummy_designer_template('Event template 2', event=dummy_event)
    regform_1 = create_regform(dummy_event, title='Registration Form 1')
    regform_2 = create_regform(dummy_event, title='Registration Form 2')

    assert get_printable_event_templates(regform_1) == [event_template_1, event_template_2]
    assert get_printable_event_templates(regform_2) == [event_template_1, event_template_2]

    event_template_1.link_regform(regform_1)
    event_template_2.link_regform(regform_2)
    assert get_printable_event_templates(regform_1) == [event_template_1]
    assert get_printable_event_templates(regform_2) == [event_template_2]


def test_can_link_to_regform_category_template(dummy_category, dummy_regform, create_dummy_designer_template):
    """Category templates cannot be linked to registration forms."""
    template = create_dummy_designer_template('Template', category=dummy_category)
    assert not can_link_to_regform(template, dummy_regform)


def test_can_link_to_regform_poster(dummy_event, dummy_regform, create_dummy_designer_template):
    """Posters cannot be linked to registration forms."""
    template = create_dummy_designer_template('Poster', event=dummy_event, type=TemplateType.poster)
    assert not can_link_to_regform(template, dummy_regform)


def test_can_link_to_regform_already_linked(dummy_event, dummy_regform, create_dummy_designer_template):
    template = create_dummy_designer_template('Template', event=dummy_event)
    template.link_regform(dummy_regform)
    assert not can_link_to_regform(template, dummy_regform)


def test_can_link_to_regform_with_backside_1(dummy_event, create_regform, create_dummy_designer_template):
    """Ensure that if the template to be linked has a backside, it must be linked to the same registration form."""
    regform_1 = create_regform(dummy_event, title='Registration Form 1')
    regform_2 = create_regform(dummy_event, title='Registration Form 2')
    frontside = create_dummy_designer_template('Frontside', event=dummy_event)
    backside = create_dummy_designer_template('Backside', event=dummy_event)
    frontside.backside_template = backside

    backside.link_regform(regform_2)
    assert not can_link_to_regform(frontside, regform_1)
    assert can_link_to_regform(frontside, regform_2)


def test_can_link_to_regform_with_backside_2(dummy_event, create_regform, create_dummy_designer_template):
    """Ensure that if the template to be linked has a backside, it must be linked to the same registration form."""
    regform_1 = create_regform(dummy_event, title='Registration Form 1')
    regform_2 = create_regform(dummy_event, title='Registration Form 2')
    frontside_1 = create_dummy_designer_template('Frontside 1', event=dummy_event)
    frontside_2 = create_dummy_designer_template('Frontside 2', event=dummy_event)
    backside = create_dummy_designer_template('Backside', event=dummy_event)
    frontside_1.backside_template = backside
    frontside_2.backside_template = backside

    # Frontside templates are not linked to any regform, so backside can be linked to any regform
    assert can_link_to_regform(backside, regform_1)
    assert can_link_to_regform(backside, regform_2)

    frontside_1.link_regform(regform_1)
    # frontside_1 is linked to regform 2, so backside can only be linked to regform_1
    assert can_link_to_regform(backside, regform_1)
    assert not can_link_to_regform(backside, regform_2)
