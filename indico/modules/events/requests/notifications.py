# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask_pluginengine import plugin_context

from indico.core.notifications import email_sender


def _make_email(req, template, *, to_request_managers: bool):
    with plugin_context(req.definition.plugin):
        return req.definition.make_notification_email(req, template, to_request_managers=to_request_managers)


def _get_template_module(name, req, **context):
    """Get template module for a request email notification template.

    :param name: template name
    :param req: :class:`Request` instance
    :param context: data passed to the template
    """
    context['req'] = req
    return req.definition.get_notification_template(name, **context)


def notify_request_managers(req, template, **context):
    """Notify request managers about something.

    :param req: the :class:`Request`
    :param template: the template for the notification
    :param context: data passed to the template
    """
    context['event'] = req.event
    context['req'] = req
    with req.event.force_event_locale():
        tpl_request_managers = _get_template_module(template, **context)
        return _make_email(req, tpl_request_managers, to_request_managers=True)


def notify_event_managers(req, template, **context):
    """Notify event managers about something.

    :param req: the :class:`Request`
    :param template: the template for the notification
    :param context: data passed to the template
    """
    context['event'] = req.event
    context['req'] = req
    with req.event.force_event_locale():
        tpl_event_managers = _get_template_module(template, **context)
        return _make_email(req, tpl_event_managers, to_request_managers=False)


@email_sender
def notify_new_modified_request(req, new):
    """Notify event managers and request managers about a new/modified request.

    :param req: the :class:`Request`
    :param new: True if it's a new request
    """
    yield notify_event_managers(req, 'new_modified_to_event_managers.txt', new=new)
    yield notify_request_managers(req, 'new_modified_to_request_managers.txt', new=new)


@email_sender
def notify_withdrawn_request(req, email_event_managers):
    """Notify event managers and request managers about a withdrawn request.

    :param req: the :class:`Request`
    :param email_event_managers: if event managers should be notified
    """
    if email_event_managers:
        yield notify_event_managers(req, 'withdrawn_to_event_managers.txt')
    yield notify_request_managers(req, 'withdrawn_to_request_managers.txt')


@email_sender
def notify_accepted_request(req):
    """Notify event managers and request managers about a accepted request.

    :param req: the :class:`Request`
    """
    yield notify_event_managers(req, 'accepted_to_event_managers.txt')
    yield notify_request_managers(req, 'accepted_to_request_managers.txt')


@email_sender
def notify_rejected_request(req):
    """Notify event managers and request managers about a rejected request.

    :param req: the :class:`Request`
    """
    yield notify_event_managers(req, 'rejected_to_event_managers.txt')
    yield notify_request_managers(req, 'rejected_to_request_managers.txt')
