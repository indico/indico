# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.modules.events.registration.util import ActionMenuEntry
from indico.modules.receipts.util import can_user_manage_receipt_templates, has_any_receipts
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


@signals.menu.items.connect_via('admin-sidemenu')
def _admin_sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('receipts', _('Document Templates'), url_for('receipts.admin_settings'),
                           section='customization')


@signals.menu.items.connect_via('event-management-sidemenu')
def _event_sidemenu_items(sender, event, **kwargs):
    if can_user_manage_receipt_templates(session.user):
        return SideMenuItem('receipts', _('Document Templates'), url_for('receipts.template_list', event),
                            section='customization')


@signals.menu.items.connect_via('category-management-sidemenu')
def _category_sidemenu_items(sender, category, **kwargs):
    if can_user_manage_receipt_templates(session.user):
        return SideMenuItem('receipts', _('Document Templates'), url_for('receipts.template_list', category),
                            icon='agreement', weight=20)


@signals.event.registrant_list_action_menu.connect
def _get_action_menu_items(regform, **kwargs):
    has_templates = regform.event.has_receipt_templates()
    if has_templates:
        yield ActionMenuEntry(
            _('Generate Documents'),
            'agreement',
            type='callback',
            callback='printReceipts',
            params={'event_id': regform.event_id},
            weight=70
        )
    # show download options even if there are no files, because the disabled option indicates
    # to event organizers that the possibility to bulk-download them exists
    if has_templates or has_any_receipts(regform):
        yield ActionMenuEntry(
            _('Download Documents (Single PDF)'),
            'agreement',
            type='href-custom',
            url=url_for('.registrations_receipts_export', regform, combined=1),
            extra_classes='js-submit-list-form regform-download-documents',
            weight=69,  # 😏 (pure coincidence, really!) i needed "right after 'generate'" which happened to be 70
        )
        yield ActionMenuEntry(
            _('Download Documents (Separate PDFs)'),
            'agreement',
            type='href-custom',
            url=url_for('.registrations_receipts_export', regform),
            extra_classes='js-submit-list-form regform-download-documents',
            weight=68,
        )
