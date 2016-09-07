# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.dialects.postgresql import ARRAY, JSON

from indico.core.db import db
from indico.util.locators import locator_property


def _get_next_position(context):
    """Get the next email template position for the event."""
    event_id = context.current_parameters['event_id']
    res = db.session.query(db.func.max(AbstractEmailTemplate.position)).filter_by(event_id=event_id).one()
    return (res[0] or 0) + 1


class AbstractEmailTemplate(db.Model):
    """Represents an email template for abstracts notifications."""

    __tablename__ = 'email_templates'
    __table_args__ = {'schema': 'event_abstracts'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The relative position of the template in the list of templates
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    #: The address to use as Reply-To in the email
    reply_to_address = db.Column(
        db.String,
        nullable=False
    )
    #: The subject of the email
    subject = db.Column(
        db.String,
        nullable=False
    )
    #: The body of the template
    body = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: List of extra email addresses to be added as CC in the email
    extra_cc_emails = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[],
    )
    #: Whether to include the submitter's email address as To for emails
    include_submitter = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether to include authors' email addresses as To for emails
    include_authors = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether to include co-authors' email addresses as CC for emails
    include_coauthors = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether to stop checking the rest of the conditions when a match is found
    stop_on_match = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: Conditions need to be met to send the email
    rules = db.Column(
        JSON,
        nullable=False
    )

    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'abstract_email_templates',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - logs (AbstractEmailLogEntry.email_template)

    @property
    def to_emails(self):
        emails = {}
        if self.include_authors:
            # TODO: get list of abstract's authors
            authors_emails = {}
            emails.update(authors_emails)
        if self.include_submitter:
            # TODO: get email of abstract's submitter
            submitter_email = ''
            emails.add(submitter_email)
        return emails

    @property
    def cc_emails(self):
        emails = set(self.extra_cc_emails)
        if self.include_coauthors:
            # TODO: get list of abstract's co-authors
            coauthors_emails = {}
            emails.update(coauthors_emails)
        return emails

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, email_tpl_id=self.id)
