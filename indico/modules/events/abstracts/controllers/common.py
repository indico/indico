# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from operator import attrgetter

from flask import redirect
from werkzeug.exceptions import NotFound

from indico.core.config import config
from indico.legacy.pdfinterface.latex import AbstractsToPDF, ConfManagerAbstractsToPDF
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.util import generate_spreadsheet_from_abstracts
from indico.modules.events.util import ZipGeneratorMixin
from indico.util.fs import secure_filename
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.util import send_file
from indico.web.util import jsonify_data, jsonify_template


class DisplayAbstractListMixin:
    """Display the list of abstracts."""

    view_class = None
    template = None

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        return self._render_template(**self.list_generator.get_list_kwargs())

    def _render_template(self, **kwargs):
        can_download_attachments = self.event.cfa.allow_attachments
        if not can_download_attachments:
            can_download_attachments = (AbstractFile.query
                                        .filter(AbstractFile.abstract.has(event=self.event, is_deleted=False))
                                        .has_rows())
        return self.view_class.render_template(self.template, self.event,
                                               can_download_attachments=can_download_attachments, **kwargs)


class CustomizeAbstractListMixin:
    """Filter options and columns to display for the abstract list of an event."""

    view_class = None

    def _process_GET(self):
        list_config = self.list_generator._get_config()
        return jsonify_template('events/abstracts/management/abstract_list_filter.html',
                                visible_items=list_config['items'],
                                static_items=self.list_generator.static_items,
                                extra_filters=self.list_generator.extra_filters,
                                contrib_fields=self.list_generator.get_all_contribution_fields(),
                                filters=list_config['filters'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())


class AbstractsExportPDFMixin:
    """Export list of abstracts as PDF."""

    def _process(self):
        if not config.LATEX_ENABLED:
            raise NotFound
        sorted_abstracts = sorted(self.abstracts, key=attrgetter('friendly_id'))
        cls = ConfManagerAbstractsToPDF if self.management else AbstractsToPDF
        pdf = cls(self.event, sorted_abstracts)
        return send_file('abstracts.pdf', pdf.generate(), 'application/pdf')


class _AbstractsExportBaseMixin:
    """Base mixin for all abstract list spreadsheet export mixins."""

    def _generate_spreadsheet(self):
        export_config = self.list_generator.get_list_export_config()
        return generate_spreadsheet_from_abstracts(self.abstracts, export_config['static_item_ids'],
                                                   export_config['dynamic_items'])


class AbstractsExportCSV(_AbstractsExportBaseMixin):
    """Export list of abstracts to CSV."""

    def _process(self):
        return send_csv('abstracts.csv', *self._generate_spreadsheet())


class AbstractsExportExcel(_AbstractsExportBaseMixin):
    """Export list of abstracts to XLSX."""

    def _process(self):
        return send_xlsx('abstracts.xlsx', *self._generate_spreadsheet(), tz=self.event.tzinfo)


class AbstractsDownloadAttachmentsMixin(ZipGeneratorMixin):
    """Generate a ZIP file with attachment files for a given list of abstracts."""

    def _prepare_folder_structure(self, item):
        abstract_title = secure_filename(f'{item.abstract.friendly_id}_{item.abstract.title}', 'abstract')
        file_name = secure_filename(f'{item.id}_{item.filename}', str(item.id))
        return os.path.join(*self._adjust_path_length([abstract_title, file_name]))

    def _iter_items(self, abstracts):
        for abstract in abstracts:
            yield from abstract.files

    def _process(self):
        return self._generate_zip_file(self.abstracts, name_prefix='abstract-attachments',
                                       name_suffix=self.event.id)
