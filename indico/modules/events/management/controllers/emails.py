# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, session
from marshmallow import fields, validate
from webargs.flaskparser import abort

from indico.core.notifications import make_email, send_email
from indico.modules.events.contributions.models.persons import AuthorType
from indico.util.i18n import _
from indico.util.marshmallow import LowercaseString, no_relative_urls, not_empty
from indico.util.placeholders import get_sorted_placeholders, replace_placeholders
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.util import ExpectedError


class EmailRolesMetadataMixin:
    """Get the metadata for emails to abstract/contribution roles."""

    object_context = None  # contributions / abstracts

    def _process(self):
        with self.event.force_event_locale():
            tpl = get_template_module('events/persons/emails/generic.html', event=self.event)
            body = tpl.get_html_body()
            subject = tpl.get_subject()
        placeholders = get_sorted_placeholders('event-persons-email', event=None, person=None,
                                               object_context=self.object_context)
        return jsonify({
            'senders': list(self.event.get_allowed_sender_emails().items()),
            'body': body,
            'subject': subject,
            'placeholders': [p.serialize(event=None, person=None, object_context=self.object_context)
                             for p in placeholders],
        })


class EmailRolesPreviewMixin:
    """Preview an email to abstract/contribution roles."""

    object_context = None  # contributions / abstracts

    def get_placeholder_kwargs(self):
        # must return a dict containing `person` and `abstract`/`contribution`
        raise NotImplementedError

    @use_kwargs({
        'body': fields.String(required=True),
        'subject': fields.String(required=True),
    })
    def _process(self, body, subject):
        kwargs = self.get_placeholder_kwargs()
        email_body = replace_placeholders('event-persons-email', body, event=self.event,
                                          object_context=self.object_context, **kwargs)
        email_subject = replace_placeholders('event-persons-email', subject, event=self.event,
                                             object_context=self.object_context, **kwargs)
        tpl = get_template_module('events/persons/emails/custom_email.html', email_subject=email_subject,
                                  email_body=email_body)
        return jsonify(subject=tpl.get_subject(), body=tpl.get_body())


class EmailRolesSendMixin:
    """Send emails to abstract/contribution roles."""

    object_context = None  # contributions / abstracts
    log_module = None

    def get_recipients(self, roles):
        # must return an iterable of `(email, kwargs, log_metadata)` tuples
        # - `kwargs` must contain `person` and `abstract`/`contribution`
        # - `log_metadata` may be a dict of logging metadata
        raise NotImplementedError

    def get_roles_from_person_link(self, person_link):
        roles = set()
        if getattr(person_link, 'is_submitter', False):
            # ContributionPersonLink has a property that checks the ACL
            roles.add('submitter')
        if person_link.is_speaker:
            roles.add('speaker')
        if person_link.author_type == AuthorType.primary:
            roles.add('author')
        if person_link.author_type == AuthorType.secondary:
            roles.add('coauthor')
        return roles

    @use_kwargs({
        'from_address': fields.String(required=True, validate=not_empty),
        'body': fields.String(required=True, validate=[not_empty, no_relative_urls]),
        'subject': fields.String(required=True, validate=not_empty),
        'bcc_addresses': fields.List(LowercaseString(validate=validate.Email()), load_default=lambda: []),
        'copy_for_sender': fields.Bool(load_default=False),
        'recipient_roles': fields.List(
            fields.String(validate=validate.OneOf(['speaker', 'author', 'coauthor', 'submitter'])),
            required=True,
            validate=not_empty
        )
    })
    def _process(self, from_address, body, subject, bcc_addresses, copy_for_sender, recipient_roles):
        recipient_roles = frozenset(recipient_roles)
        if from_address not in self.event.get_allowed_sender_emails():
            abort(422, messages={'from_address': ['Invalid sender address']})
        count = 0
        for email, kwargs, log_metadata in self.get_recipients(recipient_roles):
            email_body = replace_placeholders('event-persons-email', body, event=self.event,
                                              object_context=self.object_context, **kwargs)
            email_subject = replace_placeholders('event-persons-email', subject, event=self.event,
                                                 object_context=self.object_context, **kwargs)
            bcc = {session.user.email} if copy_for_sender else set()
            bcc.update(bcc_addresses)
            with self.event.force_event_locale():
                tpl = get_template_module('emails/custom.html', subject=email_subject, body=email_body)
                email_data = make_email(to_list=email, bcc_list=bcc, from_address=from_address, template=tpl, html=True)
            send_email(email_data, self.event, self.log_module, log_metadata=log_metadata)
            count += 1
        if not count:
            raise ExpectedError(_('There are no people matching your selected recipient roles.'))
        return jsonify(count=count)
