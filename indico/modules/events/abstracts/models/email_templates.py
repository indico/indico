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

from indico.core.db import db
from indico.modules.events.email_templates import EmailTemplateBase


class AbstractEmailTemplate(EmailTemplateBase):
    """Represents an email template for abstracts notifications"""

    __tablename__ = 'email_templates'
    __table_args__ = {'schema': 'event_abstracts'}
    events_backref_name = 'abstract_email_templates'

    #: Whether to include authors' email addresses as To for emails
    include_authors = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether to include the submitter's email address as To for emails
    include_submitter = db.Column(
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
        emails = super(AbstractEmailTemplate, self).cc_emails
        if self.include_coauthors:
            # TODO: get list of abstract's co-authors
            coauthors_emails = {}
            emails.update(coauthors_emails)
        return emails
