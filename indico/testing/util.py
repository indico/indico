# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import operator
import re
from itertools import imap, product


def bool_matrix(template, mask=None, expect=None):
    """Creates a boolean matrix suitable for parametrized tests.

    This function lets you create a boolean matrix with certain columns being
    fixed to a static value or certain combinations being skipped. It also adds
    a last column with a value that's either fixed or depending on the other values.

    By default any `0` or `1` in the template results in its column being fixed
    to that value while any `.` column is dynamic and is used when creating all
    possible boolean values::

    >>> bool_matrix('10..', expect=True)
    ((True, False, True,  True,  True),
     (True, False, True,  False, True),
     (True, False, False, True,  True),
     (True, False, False, False, True))

    The `expect` param can be a boolean value if you always want the same value,
    a tuple if you want only a single row to be true or a callable receiving the
    whole row. In some cases the builtin callables `any` or `all` are appropriate
    callables, in other cases a custom (lambda) function is necessary. You can also
    pass the strings `any_dynamic` or `all_dynamic` which are similar to `any`/`all`
    but only check entries which do not have a fixed value in the template.

    In exclusion mode any row matching the template is skipped. It can be enabled
    by prefixing the template with a `!` character::

    >>> bool_matrix('!00.', expect=all)
    ((True,  True,  True,  True),
     (True,  True,  False, False),
     (True,  False, True,  False),
     (True,  False, False, False),
     (False, True,  True,  False),
     (False, True,  False, False))

    You can also combine both by using the default syntax and specifying the exclusion
    mask separately::

    >>> bool_matrix('..1.', mask='00..', expect=all)
    ((True,  True,  True, True,  True),
     (True,  True,  True, False, False),
     (True,  False, True, True,  False),
     (True,  False, True, False, False),
     (False, True,  True, True,  False),
     (False, True,  True, False, False))

    :param template: row template
    :param expect: string, bool value, tuple or callable
    :param mask: exclusion mask
    """
    template = template.replace(' ', '')
    exclude_all = False
    if template[0] == '!':
        exclude_all = True
        template = template[1:]
    if mask:
        if exclude_all:
            raise ValueError('cannot combine ! with mask')
        if len(mask) != len(template):
            raise ValueError('mask length differs from template length')
        if any(x != '.' and y != '.' for x, y in zip(template, mask)):
            raise ValueError('mask cannot have a value for a fixed column')
    else:
        mask = '.' * len(template)

    mapping = {'0': False, '1': True, '.': None}
    template = tuple(imap(mapping.__getitem__, template))
    mask = tuple(imap(mapping.__getitem__, mask))
    # full truth table
    iterable = product((True, False), repeat=len(template))
    if exclude_all:
        # only use rows which have values not matching the template
        iterable = (x for x in iterable if any(x[i] != v for i, v in enumerate(template) if v is not None))
    else:
        # only use rows where all values match the template
        iterable = (x for x in iterable if all(v is None or x[i] == v for i, v in enumerate(template)))
        # exclude some rows
        if any(x is not None for x in mask):
            iterable = (x for x in iterable if any(x[i] != v for i, v in enumerate(mask) if v is not None))
    # add the "expected" value which can depend on the other values
    if expect is None:
        pass
    elif expect == 'any_dynamic':
        iterable = (x + (any(y for i, y in enumerate(x) if template[i] is None),) for x in iterable)
    elif expect == 'all_dynamic':
        iterable = (x + (all(y for i, y in enumerate(x) if template[i] is None),) for x in iterable)
    elif callable(expect):
        iterable = (x + (expect(x),) for x in iterable)
    elif isinstance(expect, (tuple, list)):
        iterable = (x + (x == expect,) for x in iterable)
    else:
        iterable = (x + (expect,) for x in iterable)
    matrix = tuple(iterable)
    if not matrix:
        raise ValueError('empty matrix')
    return matrix


def extract_emails(smtp, required=True, count=None, one=False, regex=False, **kwargs):
    """Extracts emails from an smtp outbox.

    :param smtp: The `smtp` fixture from the testcase
    :param required: Fail if no matching emails were found
    :param count: Require exactly `count` emails to be found
    :param one: Require exactly one email to be found
    :param kwargs: Header values to match against
    :return: list of emails, unless `one` is true in which
             case the matching email or `None` is returned
    """
    if one:
        if count is not None:
            raise ValueError('Cannot specify both `count` and `one`')
        count = 1
    compare = re.search if regex else operator.eq
    found = []
    for mail in smtp.outbox:
        for header, value in kwargs.iteritems():
            if not compare(value, mail[header]):
                break
        else:  # everything matched
            found.append(mail)
    found_set = set(found)
    smtp.outbox = [mail for mail in smtp.outbox if mail not in found_set]
    __tracebackhide__ = True
    if required:
        assert found, 'No matching emails found'
    if count is not None:
        assert len(found) == count, 'Expected {} emails, got {}'.format(count, len(found))
    if one:
        return found[0] if found else None
    return found


def extract_logs(caplog, required=True, count=None, one=False, regex=False, **kwargs):
    """Extracts log records from python's logging system.

    :param caplog: The `caplog` fixture from the testcase
    :param required: Fail if no matching records were found
    :param count: Require exactly `count` records to be found
    :param one: Require exactly one record to be found
    :param kwargs: LogRecord attribute values to match against
    :return: list of log records, unless `one` is true in which
             case the matching record or `None` is returned
    """
    if one:
        if count is not None:
            raise ValueError('Cannot specify both `count` and `one`')
        count = 1
    compare = re.search if regex else operator.eq
    found = []
    for record in caplog.handler.records:
        for key, value in kwargs.iteritems():
            if not compare(value, getattr(record, key)):
                break
        else:  # everything matched
            found.append(record)
    found_set = set(found)
    caplog.handler.records = [record for record in caplog.handler.records if record not in found_set]
    __tracebackhide__ = True
    if required:
        assert found, 'No matching records found'
    if count is not None:
        assert len(found) == count, 'Expected {} records, got {}'.format(count, len(found))
    if one:
        return found[0] if found else None
    return found
