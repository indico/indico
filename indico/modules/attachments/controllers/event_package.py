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

import os
import tempfile
from operator import itemgetter
from zipfile import ZipFile

from flask import session
from sqlalchemy import cast, Date

from indico.util.date_time import format_date
from indico.util.string import to_unicode
from indico.web.flask.util import send_file
from indico.modules.attachments.forms import AttachmentPackageForm
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder


class AttachmentPackageMixin:
    wp = None

    def _process(self):
        form = self._prepare_form()
        if form.validate_on_submit():
            return self._generate_zip_file(self._filter_attachments(form))

        return self.wp.render_template('generate_package.html', self._conf, form=form)

    def _prepare_form(self):
        form = AttachmentPackageForm()
        form.sessions.choices = self._load_session_data()
        form.contributions.choices = self._load_contribution_data()
        form.contributions_schedule_dates.choices = self._load_schedule_data()
        return form

    def _load_session_data(self):
        return [(session.getId(), to_unicode(session.getTitle())) for session in self._conf.getSessionList()]

    def _load_contribution_data(self):
        return [(contrib.getId(), to_unicode(contrib.getTitle())) for contrib in self._conf.getContributionList()]

    def _load_schedule_data(self):
        dates = {contrib.getStartDate().date() for contrib in self._conf.getContributionList()}
        return sorted([(unicode(d), format_date(d, 'short')) for d in dates], key=itemgetter(1))

    def _filter_attachments(self, form):
        attachments = []
        added_since = form.added_since.data
        attachments.extend(self._filter_protected(self._filter_top_level_attachments(added_since)))
        if form.sessions.data:
            attachments.extend(self._filter_protected(self._filter_by_sessions(form.sessions.data, added_since)))

        contribution_ids = set(form.contributions.data +
                               self._get_contributions_by_schedule_date(form.contributions_schedule_dates.data))
        if contribution_ids:
            attachments.extend(self._filter_protected(self._filter_by_contributions(contribution_ids, added_since)))
        return attachments

    def _filter_protected(self, attachments):
        return [attachment for attachment in attachments if attachment.can_access(session.user)]

    def _filter_top_level_attachments(self, added_since):
        query = self._build_base_query().filter(AttachmentFolder.linked_object == self._conf)

        if added_since:
            query = self._filter_by_date(query, added_since)

        return query.all()

    def _build_base_query(self):
        return Attachment.find(Attachment.type == AttachmentType.file, ~AttachmentFolder.is_deleted,
                               ~Attachment.is_deleted, AttachmentFolder.event_id == int(self._conf.getId()),
                               _join=AttachmentFolder)

    def _filter_by_sessions(self, session_ids, added_since):
        query = self._build_base_query().filter(AttachmentFolder.session_id.in_(session_ids))

        if added_since:
            query = self._filter_by_date(query, added_since)

        return query.all()

    def _get_contributions_by_schedule_date(self, dates):
        return [contribution.getId() for contribution in self._conf.getContributionList()
                if str(contribution.getStartDate().date()) in dates]

    def _filter_by_contributions(self, contribution_ids, added_since):
        query = self._build_base_query().filter(AttachmentFolder.contribution_id.in_(contribution_ids))

        if added_since:
            query = self._filter_by_date(query, added_since)

        return query.all()

    def _filter_by_date(self, query, added_since):
        return query.filter(cast(AttachmentFile.created_dt, Date) >= added_since)

    def _generate_zip_file(self, attachments):
        temp_file = tempfile.NamedTemporaryFile('w')
        with ZipFile(temp_file.name, 'w', allowZip64=True) as zip_handler:
            for attachment in attachments:
                if not attachment.folder.is_default:
                    name = os.path.join(os.path.join(secure_filename(attachment.folder.title,
                                                                     unicode(attachment.folder.id)),
                                                     attachment.file.filename))
                else:
                    name = attachment.file.filename

                with attachment.file.storage.get_local_path(attachment.file.storage_file_id) as filepath:
                    zip_handler.write(filepath, name)

        return send_file('material-{}.zip'.format(self._conf.id), temp_file.name, 'application/zip', inline=False)
