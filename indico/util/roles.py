# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import csv

from flask import flash, session

from indico.core.errors import UserValueError
from indico.modules.events.roles.forms import ImportMembersCSVForm
from indico.modules.users import User
from indico.util.i18n import _, ngettext
from indico.util.spreadsheets import csv_text_io_wrapper
from indico.util.string import validate_email
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data, jsonify_template


class ImportRoleMembersMixin:
    """Import members from a CSV file into a role."""

    logger = None

    def import_members_from_csv(self, f):
        with csv_text_io_wrapper(f) as ftxt:
            reader = csv.reader(ftxt.read().splitlines())

        emails = set()
        for num_row, row in enumerate(reader, 1):
            if len(row) != 1:
                raise UserValueError(_('Row {}: malformed CSV data').format(num_row))
            email = row[0].strip().lower()

            if email and not validate_email(email):
                raise UserValueError(_('Row {row}: invalid email address: {email}').format(row=num_row, email=email))
            if email in emails:
                raise UserValueError(_('Row {}: email address is not unique').format(num_row))
            emails.add(email)

        users = set(User.query.filter(~User.is_deleted, User.all_emails.in_(emails)))
        users_emails = {user.email for user in users}
        unknown_emails = emails - users_emails
        new_members = users - self.role.members
        return new_members, users, unknown_emails

    def _process(self):
        form = ImportMembersCSVForm()

        if form.validate_on_submit():
            new_members, users, unknown_emails = self.import_members_from_csv(form.source_file.data)
            if form.remove_existing.data:
                deleted_members = self.role.members - users
                for member in deleted_members:
                    self.logger.info(f'User {member} removed from role {self.role} by {session.user}')
                self.role.members = users
            else:
                self.role.members |= users
            for user in new_members:
                self.logger.info(f'User {user} added to role {self.role} by {session.user}')
            flash(ngettext('{} member has been imported.',
                           '{} members have been imported.',
                           len(users)).format(len(users)), 'success')
            if unknown_emails:
                flash(ngettext('There is no user with this email address: {}',
                               'There are no users with these email addresses: {}',
                               len(unknown_emails)).format(', '.join(unknown_emails)), 'warning')
            tpl = get_template_module('events/roles/_roles.html')
            return jsonify_data(html=tpl.render_role(self.role, collapsed=False, email_button=False))
        return jsonify_template('events/roles/import_members.html', form=form, role=self.role)
