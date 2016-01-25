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

import csv
import re
from io import BytesIO

from speaklater import is_lazy_string
from xlsxwriter import Workbook

from indico.web.flask.util import send_file


def _prepare_csv_data(data, _linebreak_re=re.compile(r'(\r?\n)+')):
    if isinstance(data, (list, tuple)):
        data = ', '.join(data)
    elif isinstance(data, set):
        data = ', '.join(sorted(data, key=unicode.lower))
    elif isinstance(data, bool):
        data = 'Yes' if data else 'No'
    elif data is None:
        data = ''
    return _linebreak_re.sub('    ', unicode(data)).encode('utf-8')


def generate_csv(headers, rows):
    """Generates a CSV file from a list of headers and rows.

    While CSV cells may contain multiline data, we replace linebreaks
    with spaces in case someone wants to use it in Excel which does
    *not* handle such cells properly...

    :param headers: a list of cell captions
    :param rows: a list of dicts mapping captions to values
    :return: an `io.BytesIO` containing the CSV data
    """
    buf = BytesIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _prepare_csv_data(v) for k, v in row.iteritems()})
    buf.seek(0)
    return buf


def _prepare_excel_data(data):
    if isinstance(data, (list, tuple)):
        data = ', '.join(data)
    elif isinstance(data, set):
        data = ', '.join(sorted(data, key=unicode.lower))
    elif is_lazy_string(data):
        data = unicode(data)
    return data


def generate_xlsx(headers, rows):
    """Generates an XLSX file from a list of headers and rows.

    :param headers: a list of cell captions
    :param rows: a list of dicts mapping captions to values
    :return: an `io.BytesIO` containing the XLSX data
    """
    workbook_options = {'in_memory': True, 'strings_to_formulas': False, 'strings_to_numbers': False}
    buf = BytesIO()
    header_positions = {name: i for i, name in enumerate(headers)}
    # convert row dicts to lists
    rows = [[x[1] for x in sorted(row.items(), key=lambda x: header_positions[x[0]])] for row in rows]
    assert all(len(row) == len(headers) for row in rows)
    with Workbook(buf, workbook_options) as workbook:
        bold = workbook.add_format({'bold': True})
        sheet = workbook.add_worksheet()
        for col, name in enumerate(headers):
            sheet.write(0, col, name, bold)
        for row, values in enumerate(rows, 1):
            sheet.write_row(row, 0, map(_prepare_excel_data, values))
    buf.seek(0)
    return buf


def send_csv(filename, headers, rows):
    """Sends a CSV file to the client

    :param filename: The name of the CSV file
    :param headers: a list of cell captions
    :param rows: a list of dicts mapping captions to values
    :return: a flask response containing the CSV data
    """
    buf = generate_csv(headers, rows)
    return send_file(filename, buf, 'text/csv', inline=False)


def send_xlsx(filename, headers, rows):
    """Sends an XLSX file to the client

    :param filename: The name of the CSV file
    :param headers: a list of cell captions
    :param rows: a list of dicts mapping captions to values
    :return: a flask response containing the XLSX data
    """
    buf = generate_xlsx(headers, rows)
    return send_file(filename, buf, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', inline=False)
