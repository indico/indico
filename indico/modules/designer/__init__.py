# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from reportlab.lib import pagesizes
from reportlab.lib.units import mm

from indico.core import signals
from indico.util.enum import RichIntEnum
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


class TemplateType(RichIntEnum):
    __titles__ = [None, _('Badge'), _('Poster')]
    badge = 1
    poster = 2


class PageOrientation(RichIntEnum):
    __titles__ = [None, _('Landscape'), _('Portrait')]
    landscape = 1
    portrait = 2


class PageSize(RichIntEnum):
    __titles__ = [None, 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'Letter', 'A6', 'ID-1']
    __page_sizes__ = {
        'A0': pagesizes.A0,
        'A1': pagesizes.A1,
        'A2': pagesizes.A2,
        'A3': pagesizes.A3,
        'A4': pagesizes.A4,
        'A5': pagesizes.A5,
        'A6': pagesizes.A6,
        'letter': pagesizes.LETTER,
        # https://www.iso.org/standard/31432.html
        'ID_1': (53.98*mm, 85.6*mm),
    }

    A0 = 1
    A1 = 2
    A2 = 3
    A3 = 4
    A4 = 5
    A5 = 6
    letter = 7
    A6 = 8
    ID_1 = 9

    @property
    def size(self):
        return self.__page_sizes__[self.name]


class PageLayout(RichIntEnum):
    __titles__ = [None, _('Single sided (foldable)'), _('Double sided'), _('Only front side')]
    foldable = 1
    double_sided = 2
    front_only = 3


DEFAULT_CONFIG = {
    TemplateType.poster: {
        'tpl_size': [1050, 1484],  # A4 50 px/cm
        'zoom_factor': 0.5,
        'disallow_groups': ('registrant', 'regform_fields')
    },
    TemplateType.badge: {
        'tpl_size': [425, 270],  # A4 50 px/cm
        'zoom_factor': 1,
        'disallow_groups': ()
    }
}


@signals.core.get_placeholders.connect_via('designer-fields')
def _get_designer_placeholders(sender, regform=None, **kwargs):
    from indico.modules.designer import placeholders
    for name in placeholders.__all__:
        obj = getattr(placeholders, name)
        if isinstance(obj, type) and issubclass(obj, placeholders.DesignerPlaceholder) and hasattr(obj, 'name'):
            yield obj

    if regform:
        from indico.modules.designer.placeholders import RegistrationFormFieldPlaceholder
        from indico.modules.events.registration.models.items import RegistrationFormItemType
        for field in regform.active_fields:
            # Personal data fields are already included in the 'registrant' group
            if field.type != RegistrationFormItemType.field_pd:
                yield RegistrationFormFieldPlaceholder(field=field)


@signals.menu.items.connect_via('event-management-sidemenu')
def _event_sidemenu_items(sender, event, **kwargs):
    if event.can_manage(session.user):
        return SideMenuItem('designer', _('Posters/Badges'), url_for('designer.template_list', event),
                            section='customization')


@signals.menu.items.connect_via('category-management-sidemenu')
def _category_sidemenu_items(sender, category, **kwargs):
    if category.can_manage(session.user):
        return SideMenuItem('designer', _('Posters/Badges'), url_for('designer.template_list', category),
                            icon='palette', weight=30)
