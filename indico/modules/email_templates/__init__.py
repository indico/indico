# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


@signals.menu.items.connect_via('event-management-sidemenu')
def _event_sidemenu_items(sender, event, **kwargs):
    if event.can_manage(session.user):
        return SideMenuItem('email_templates', _('Email templates'),
                            url_for('email_templates.email_template_list', event),
                            section='customization')


@signals.menu.items.connect_via('category-management-sidemenu')
def _category_sidemenu_items(sender, category, **kwargs):
    if category.can_manage(session.user):
        return SideMenuItem('email_templates', _('Email templates'),
                            url_for('email_templates.email_template_list', category),
                            weight=30, icon='user-reading')
