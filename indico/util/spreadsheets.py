# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import csv
import re
from contextlib import contextmanager
from datetime import date, datetime
from enum import auto
from io import BytesIO, TextIOWrapper

from markupsafe import Markup
from speaklater import is_lazy_string
from xlsxwriter import Workbook

from indico.core.errors import UserValueError
from indico.util.enum import RichStrEnum
from indico.util.i18n import _
from indico.web.flask.util import send_file


class CSVFieldDelimiter(RichStrEnum):
    __titles__ = {
        'comma': _('Comma'),
        'semicolon': _('Semicolon'),
        'tab': _('Tab'),
        'space': _('Space')
    }
    __delimiters__ = {
        'comma': ',',
        'semicolon': ';',
        'tab': '\t',
        'space': ' ',
    }

    comma = auto()
    semicolon = auto()
    tab = auto()
    space = auto()

    @property
    def delimiter(self):
        return self.__delimiters__[self.name]


def unique_col(name, id_):
    """Ensure uniqueness of a header/data entry.

    Simply apply this to both the entry in `headers` and the
    dict keys in `rows` before passing them to one of the spreadsheet
    functions.

    :param name: The actual column name/title
    :param id_: The id or whatever is needed to ensure uniqueness
    """
    return name, id_


def _prepare_header(header):
    if isinstance(header, tuple):
        header = header[0]
    return header


def _prepare_csv_data(data, _linebreak_re=re.compile(r'(\r?\n)+'), _dangerous_chars_re=re.compile(r'^[=+@-]+')):
    if isinstance(data, (list, tuple)):
        data = '; '.join(data)
    elif isinstance(data, set):
        data = '; '.join(sorted(data, key=str.lower))
    elif isinstance(data, bool):
        data = 'Yes' if data else 'No'
    elif data is None:
        data = ''
    data = _linebreak_re.sub('    ', str(data))
    # https://www.owasp.org/index.php/CSV_Injection
    # quoting the cell's value does NOT mitigate this, so we need to strip
    # those characters from the beginning...
    return _dangerous_chars_re.sub('', data)


@contextmanager
def csv_text_io_wrapper(buf):
    """IO wrapper to use the csv reader/writer on a byte stream."""
    w = TextIOWrapper(buf, encoding='utf-8-sig', newline='')
    try:
        yield w
    except UnicodeDecodeError:
        raise UserValueError(_('The CSV file must be saved in UTF-8 encoding'))
    finally:
        w.detach()


def generate_csv(headers, rows, *, include_header=True):
    """Generate a CSV file from a list of headers and rows.

    While CSV cells may contain multiline data, we replace linebreaks
    with spaces in case someone wants to use it in Excel which does
    *not* handle such cells properly...

    :param headers: a list of cell captions
    :param rows: a list of dicts mapping captions to values
    :param include_header: whether to include a header in the data
    :return: an `io.BytesIO` containing the CSV data
    """
    buf = BytesIO()
    with csv_text_io_wrapper(buf) as csvbuf:
        writer = csv.writer(csvbuf)
        if include_header:
            writer.writerow(map(_prepare_header, headers))
        header_positions = {name: i for i, name in enumerate(headers)}
        assert all(len(row) == len(headers) for row in rows)
        for row in rows:
            row = sorted(row.items(), key=lambda x: header_positions[x[0]])
            writer.writerow([_prepare_csv_data(v) for k, v in row])
    buf.seek(0)
    return buf


def _prepare_excel_data(data):
    if isinstance(data, (list, tuple)):
        data = '; '.join(data)
    elif isinstance(data, set):
        data = '; '.join(sorted(data, key=str.lower))
    elif is_lazy_string(data) or isinstance(data, Markup):
        data = str(data)
    return data


def generate_xlsx(headers, rows, tz=None):
    """Generate an XLSX file from a list of headers and rows.

    :param headers: a list of cell captions
    :param rows: a list of dicts mapping captions to values
    :return: an `io.BytesIO` containing the XLSX data
    """
    workbook_options = {'in_memory': True, 'strings_to_formulas': False, 'strings_to_numbers': False,
                        'strings_to_urls': False}
    buf = BytesIO()
    header_positions = {name: i for i, name in enumerate(headers)}
    # convert row dicts to lists
    rows = [[x[1] for x in sorted(row.items(), key=lambda x: header_positions[x[0]])] for row in rows]
    assert all(len(row) == len(headers) for row in rows)
    with Workbook(buf, workbook_options) as workbook:
        bold = workbook.add_format({'bold': True})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        datetime_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm'})
        sheet = workbook.add_worksheet()
        for col, name in enumerate(map(_prepare_header, headers)):
            sheet.write(0, col, name, bold)
        for row, values in enumerate(rows, 1):
            for col, data in enumerate(values):
                if isinstance(data, datetime):
                    sheet.write_datetime(row, col, data.astimezone(tz).replace(tzinfo=None), datetime_format)
                elif isinstance(data, date):
                    sheet.write_datetime(row, col, data, date_format)
                else:
                    sheet.write(row, col, _prepare_excel_data(data))
    buf.seek(0)
    return buf


def send_csv(filename, headers, rows, *, include_header=True):
    """Send a CSV file to the client.

    :param filename: The name of the CSV file
    :param headers: a list of cell captions
    :param rows: a list of dicts mapping captions to values
    :param include_header: whether to include a header in the data
    :return: a flask response containing the CSV data
    """
    buf = generate_csv(headers, rows, include_header=include_header)
    return send_file(filename, buf, 'text/csv', inline=False)


def send_xlsx(filename, headers, rows, tz=None):
    """Send an XLSX file to the client.

    :param filename: The name of the CSV file
    :param headers: a list of cell captions
    :param rows: a list of dicts mapping captions to values
    :param tz: the timezone for the values that are datetime objects
    :return: a flask response containing the XLSX data
    """
    buf = generate_xlsx(headers, rows, tz=tz)
    return send_file(filename, buf, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', inline=False)
