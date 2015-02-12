# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from flask_pluginengine import plugin_context

from indico.core.config import Config
from indico.core.notifications import email_sender, make_email


def _get_event_manager_emails(event):
    """Get set of event manager emails"""
    # XXX: doesn't this make much more sense as a method in the Conference class?
    return {event.getCreator().getEmail()} | {u.getEmail() for u in event.getManagerList()}


def _get_request_manager_emails(req):
    """Get set of request manager emails"""
    with plugin_context(req.definition.plugin):
        return req.definition.get_manager_notification_emails()


def _get_template_module(name, req, **context):
    """Get template module for a request email notification template

    :param name: template name
    :param req: :class:`Request` instance
    :param context: data passed to the template
    """
    context['req'] = req
    return req.definition.get_notification_template(name, **context)


def _notify_managers(req, event_manager_tpl, request_manager_tpl, **context):
    """Notifies event managers and request managers about new/modified request

    :param req: the :class:`Request`
    :param event_manager_tpl: the template for the event manager notification
    :param request_manager_tpl: the template for the request manager notification
    :param context: data passed to the templates
    """
    event = req.event
    from_addr = Config.getInstance().getSupportEmail()
    event_manager_emails = _get_event_manager_emails(event) if event_manager_tpl else None
    request_manager_emails = _get_request_manager_emails(req)
    context['event'] = event
    context['req'] = req
    tpl_event_managers = _get_template_module(event_manager_tpl, **context) if event_manager_tpl else None
    tpl_request_managers = _get_template_module(request_manager_tpl, **context)
    if tpl_event_managers:
        yield make_email(event_manager_emails, from_address=from_addr,
                         subject=tpl_event_managers.get_subject(), body=tpl_event_managers.get_body())
    if request_manager_emails:
        yield make_email(request_manager_emails, from_address=from_addr,
                         subject=tpl_request_managers.get_subject(), body=tpl_request_managers.get_body())


@email_sender
def notify_new_modified_request(req, new):
    """Notifies event managers and request managers about a new/modified request

    :param req: the :class:`Request`
    :param new: True if it's a new request
    """
    return _notify_managers(req, 'new_modified_to_event_managers.txt', 'new_modified_to_request_managers.txt', new=new)


@email_sender
def notify_withdrawn_request(req, notify_event_managers):
    """Notifies event managers and request managers about a withdrawn request

    :param req: the :class:`Request`
    :param notify_event_managers: if event managers should be notified
    """
    return _notify_managers(req, 'withdrawn_to_event_managers.txt' if notify_event_managers else None,
                            'withdrawn_to_request_managers.txt')


@email_sender
def notify_accepted_request(req):
    """Notifies event managers and request managers about a accepted request

    :param req: the :class:`Request`
    """
    return _notify_managers(req, 'accepted_to_event_managers.txt', 'accepted_to_request_managers.txt')


@email_sender
def notify_rejected_request(req):
    """Notifies event managers and request managers about a rejected request

    :param req: the :class:`Request`
    """
    return _notify_managers(req, 'rejected_to_event_managers.txt', 'rejected_to_request_managers.txt')
