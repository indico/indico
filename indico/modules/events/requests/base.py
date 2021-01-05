# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask_pluginengine import plugin_context
from wtforms.fields import SubmitField, TextAreaField

from indico.core.config import config
from indico.core.db import db
from indico.modules.events.requests.notifications import (notify_accepted_request, notify_new_modified_request,
                                                          notify_rejected_request, notify_withdrawn_request)
from indico.modules.events.requests.views import WPRequestsEventManagement
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.templating import get_overridable_template_name, get_template_module
from indico.web.forms.base import FormDefaults, IndicoForm


class RequestFormBase(IndicoForm):
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.request = kwargs.pop('request')
        super(RequestFormBase, self).__init__(*args, **kwargs)


class RequestManagerForm(IndicoForm):
    action_buttons = {'action_save', 'action_accept', 'action_reject'}

    comment = TextAreaField(_('Comment'),
                            description=_('The comment will be shown only if the request is accepted or rejected.'))
    action_save = SubmitField(_('Save'))
    action_accept = SubmitField(_('Accept'))
    action_reject = SubmitField(_('Reject'))


class RequestDefinitionBase(object):
    """A service request which can be sent by event managers."""

    #: the plugin containing this request definition - assigned automatically
    plugin = None
    #: the unique internal name of the request type
    name = None
    #: the title of the request type as shown to users
    title = None
    #: the :class:`IndicoForm` to use for the request form
    form = None
    #: the :class:`IndicoForm` to use for the request manager form
    manager_form = RequestManagerForm
    #: default values to use if there's no existing request
    form_defaults = {}

    @classmethod
    def render_form(cls, event, **kwargs):
        """Render the request form.

        :param event: the event the request is for
        :param kwargs: arguments passed to the template
        """
        tpl = get_overridable_template_name('event_request_details.html', cls.plugin, 'events/requests/')
        return WPRequestsEventManagement.render_template(tpl, event, **kwargs)

    @classmethod
    def create_form(cls, event, existing_request=None):
        """Create the request form.

        :param event: the event the request is for
        :param existing_request: the :class:`Request` if there's an existing request of this type
        :return: an instance of an :class:`IndicoForm` subclass
        """
        defaults = FormDefaults(existing_request.data if existing_request else cls.form_defaults)
        with plugin_context(cls.plugin):
            return cls.form(prefix='request-', obj=defaults, event=event, request=existing_request)

    @classmethod
    def create_manager_form(cls, req):
        """Create the request management form.

        :param req: the :class:`Request` of the request
        :return: an instance of an :class:`IndicoForm` subclass
        """
        defaults = FormDefaults(req, **req.data)
        with plugin_context(cls.plugin):
            return cls.manager_form(prefix='request-manage-', obj=defaults)

    @classmethod
    def get_notification_template(cls, name, **context):
        """Get the template module for a notification email.

        :param name: the template name
        :param context: data passed to the template

        """
        tpl = get_overridable_template_name(name, cls.plugin, 'events/requests/emails/', 'emails/')
        return get_template_module(tpl, **context)

    @classmethod
    def can_be_managed(cls, user):
        """Check whether the user is allowed to manage this request type.

        :param user: a :class:`.User`
        """
        raise NotImplementedError

    @classmethod
    def get_manager_notification_emails(cls):
        """Return the email addresses of users who manage requests of this type.

        The email addresses are used only for notifications.
        It usually makes sense to return the email addresses of the users who
        pass the :method:`can_be_managed` check.

        :return: set of email addresses
        """
        return set()

    @classmethod
    def get_notification_reply_email(cls):
        """Return the *Reply-To* e-mail address for notifications."""
        return config.SUPPORT_EMAIL

    @classmethod
    def send(cls, req, data):
        """Send a new/modified request.

        :param req: the :class:`Request` of the request
        :param data: the form data from the request form
        """
        req.data = dict(req.data or {}, **data)
        is_new = req.id is None
        if is_new:
            db.session.add(req)
            db.session.flush()  # we need the creation dt for the notification
        notify_new_modified_request(req, is_new)

    @classmethod
    def withdraw(cls, req, notify_event_managers=True):
        """Withdraw the request.

        :param req: the :class:`Request` of the request
        :param notify_event_managers: if event managers should be notified
        """
        from indico.modules.events.requests.models.requests import RequestState
        req.state = RequestState.withdrawn
        notify_withdrawn_request(req, notify_event_managers)

    @classmethod
    def accept(cls, req, data, user):
        """Accept the request.

        To ensure that additional data is saved, this method should
        call :method:`manager_save`.

        :param req: the :class:`Request` of the request
        :param data: the form data from the management form
        :param user: the user processing the request
        """
        from indico.modules.events.requests.models.requests import RequestState
        cls.manager_save(req, data)
        req.state = RequestState.accepted
        req.processed_by_user = user
        req.processed_dt = now_utc()
        notify_accepted_request(req)

    @classmethod
    def reject(cls, req, data, user):
        """Reject the request.

        To ensure that additional data is saved, this method should
        call :method:`manager_save`.

        :param req: the :class:`Request` of the request
        :param data: the form data from the management form
        :param user: the user processing the request
        """
        from indico.modules.events.requests.models.requests import RequestState
        cls.manager_save(req, data)
        req.state = RequestState.rejected
        req.processed_by_user = user
        req.processed_dt = now_utc()
        notify_rejected_request(req)

    @classmethod
    def manager_save(cls, req, data):
        """Save management-specific data.

        This method is called when the management form is submitted without
        accepting/rejecting the request (which is guaranteed to be already
        accepted or rejected).

        :param req: the :class:`Request` of the request
        :param data: the form data from the management form
        """
        req.comment = data['comment']
