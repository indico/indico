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

import os
from operator import attrgetter

from flask import redirect, request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.util import generate_spreadsheet_from_abstracts
from indico.modules.events.util import ZipGeneratorMixin
from indico.util.fs import secure_filename
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.util import send_file
from indico.web.util import jsonify_data
from MaKaC.PDFinterface.conference import ConfManagerAbstractsToPDF
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class SpecificAbstractMixin:
    """Mixin for RHs that deal with a specific abstract"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract
        }
    }

    def _checkParams(self):
        self.abstract = Abstract.get_one(request.view_args['abstract_id'], is_deleted=False)

    def _checkProtection(self):
        if not self._check_abstract_protection():
            raise Forbidden

    def _check_abstract_protection(self):
        raise NotImplementedError


class RHAbstractsBase(RHConferenceBaseDisplay):
    """Base class for all abstract-related RHs"""

    CSRF_ENABLED = True
    EVENT_FEATURE = 'abstracts'

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        # Only let event managers access the management versions.
        if self.management and not self.event_new.can_manage(session.user):
            raise Forbidden

    @property
    def management(self):
        """Whether the RH is currently used in the management area"""
        return request.view_args.get('management', False)


class RHManageAbstractsBase(RHAbstractsBase, RHModificationBaseProtected):
    """
    Base class for all abstract-related RHs that require full event
    management permissions
    """

    @property
    def management(self):
        """Whether the RH is currently used in the management area"""
        return request.view_args.get('management', True)

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)
        # Only let event managers access the management versions.
        if self.management and not self.event_new.can_manage(session.user):
            raise Forbidden


class RHAbstractBase(SpecificAbstractMixin, RHAbstractsBase):
    """
    Base class for all abstract-related RHs that require read access
    to the associated abstract.
    """

    def _checkParams(self, params):
        RHAbstractsBase._checkParams(self, params)
        SpecificAbstractMixin._checkParams(self)

    def _checkProtection(self):
        RHAbstractsBase._checkProtection(self)
        SpecificAbstractMixin._checkProtection(self)

    def _check_abstract_protection(self):
        """Perform a permission check on the current abstract.

        Override this in case you want to check for more specific
        privileges than the generic "can access".
        """
        return self.abstract.can_access(session.user)


class DisplayAbstractListMixin:
    """Display the list of abstracts"""

    view_class = None
    template = None

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        return self._render_template(**self.list_generator.get_list_kwargs())

    def _render_template(self, **kwargs):
        return self.view_class.render_template(self.template, self._conf, event=self.event_new, **kwargs)


class CustomizeAbstractListMixin:
    """Filter options and columns to display for the abstract list of an event"""

    view_class = None

    def _process_GET(self):
        list_config = self.list_generator._get_config()
        return self.view_class.render_template('management/abstract_list_filter.html', self._conf,
                                               event=self.event_new, visible_items=list_config['items'],
                                               static_items=self.list_generator.static_items,
                                               extra_filters=self.list_generator.extra_filters,
                                               contrib_fields=self.list_generator.get_all_contribution_fields(),
                                               filters=list_config['filters'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())


class AbstractsExportPDFMixin:
    """Export list of abstracts to PDF"""

    def _process(self):
        sorted_abstracts = sorted(self.abstracts, key=attrgetter('friendly_id'))
        pdf = ConfManagerAbstractsToPDF(self.event_new, sorted_abstracts)
        return send_file('abstracts.pdf', pdf.generate(), 'application/pdf')


class _AbstractsExportBaseMixin:
    """Base class for all abstract list export classes"""

    def _generate_spreadsheet(self):
        export_config = self.list_generator.get_list_export_config()
        return generate_spreadsheet_from_abstracts(self.abstracts, export_config['static_item_ids'],
                                                   export_config['dynamic_items'])


class AbstractsExportCSV(_AbstractsExportBaseMixin):
    """Export list of abstracts to CSV"""

    def _process(self):
        return send_csv('abstracts.csv', *self._generate_spreadsheet())


class AbstractsExportExcel(_AbstractsExportBaseMixin):
    """Export list of abstracts to XLSX"""

    def _process(self):
        return send_xlsx('abstracts.xlsx', *self._generate_spreadsheet())


class AbstractsDownloadAttachmentsMixin(ZipGeneratorMixin):
    """Generate a ZIP file with attachment files for a given list of abstracts"""

    def _prepare_folder_structure(self, item):
        abstract_title = secure_filename('{}_{}'.format(item.abstract.title, unicode(item.abstract.id)), 'abstract')
        file_name = secure_filename('{}_{}'.format(unicode(item.id), item.filename), item.filename)
        return os.path.join(*self._adjust_path_length([abstract_title, file_name]))

    def _iter_items(self, abstracts):
        for abstract in abstracts:
            for f in abstract.files:
                yield f

    def _process(self):
        return self._generate_zip_file(self.abstracts, name_prefix='abstract-attachments',
                                       name_suffix=self.event_new.id)
