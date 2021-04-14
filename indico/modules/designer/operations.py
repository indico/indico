# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.events import EventLogKind, EventLogRealm


def update_template(template, title, data, is_clonable, backside_template_id=None, clear_background=False):
    """Update an existing template.

    :param template: The template to be updated
    :param title: An `EventType` value
    :param data: A dict containing the template data (width, height, items, etc)
    :param is_clonable: Whether it is possible to clone this template
    :param backside_template_id: The ID of the template used as a backside
    :param clear_background: Whether to remove the background image of the
                             template
    """
    if template.data['width'] != data['width'] or template.data['height'] != data['height']:
        query = DesignerTemplate.query.filter(DesignerTemplate.backside_template == template)
        for tpl in query:
            tpl.backside_template = None
            if tpl.event:
                tpl.event.log(EventLogRealm.event, EventLogKind.negative, 'Designer', 'Backside removed',
                              session.user, data={'Template': tpl.title,
                                                  'Reason': 'Dimensions of backside changed',
                                                  'Backside': template.title})
    template.title = title
    template.data = dict({'background_position': 'stretch', 'items': []}, **data)
    template.backside_template = DesignerTemplate.get(backside_template_id) if backside_template_id else None
    template.is_clonable = is_clonable

    if clear_background:
        template.background_image = None

    if template.event:
        template.event.log(EventLogRealm.event, EventLogKind.positive, 'Designer', 'Badge template updated',
                           session.user, data={'Template': template.title})
