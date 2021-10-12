# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
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
    if session.user.is_admin:
        return SideMenuItem('receipts', _('Receipt Templates'), url_for('receipts.template_list', event),
                            section='customization')


@signals.menu.items.connect_via('category-management-sidemenu')
def _category_sidemenu_items(sender, category, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('receipts', _('Receipt Templates'), url_for('receipts.template_list', category),
                            icon='agreement')
