# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
import operator
import os
import re
from email import message_from_string
from email.policy import SMTPUTF8
from itertools import product

import yaml


def bool_matrix(template, mask=None, expect=None):
    """Create a boolean matrix suitable for parametrized tests.

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
        if any(x != '.' and y != '.' for x, y in zip(template, mask, strict=True)):
            raise ValueError('mask cannot have a value for a fixed column')
    else:
        mask = '.' * len(template)

    mapping = {'0': False, '1': True, '.': None}
    template = tuple(map(mapping.__getitem__, template))
    mask = tuple(map(mapping.__getitem__, mask))
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
        iterable = ((*x, any(y for i, y in enumerate(x) if template[i] is None)) for x in iterable)
    elif expect == 'all_dynamic':
        iterable = ((*x, all(y for i, y in enumerate(x) if template[i] is None)) for x in iterable)
    elif callable(expect):
        iterable = ((*x, expect(x)) for x in iterable)
    elif isinstance(expect, (tuple, list)):
        iterable = ((*x, x == expect) for x in iterable)
    else:
        iterable = ((*x, expect) for x in iterable)
    matrix = tuple(iterable)
    if not matrix:
        raise ValueError('empty matrix')
    return matrix


def extract_emails(smtp, required=True, count=None, one=False, regex=False, **kwargs):
    """Extract emails from an smtp outbox.

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
    orig_found = set()
    for mail in smtp.outbox:
        parsed_mail = message_from_string(str(mail), policy=SMTPUTF8)
        for header, value in kwargs.items():
            if not compare(value, parsed_mail[header]):
                break
        else:  # everything matched
            found.append(parsed_mail)
            orig_found.add(mail)
    smtp.handler.outbox = [mail for mail in smtp.handler.outbox if mail not in orig_found]
    __tracebackhide__ = True
    if required:
        assert found, 'No matching emails found'
    if count is not None:
        assert len(found) == count, f'Expected {count} emails, got {len(found)}'
    if one:
        return found[0] if found else None
    return found


def extract_logs(caplog, required=True, count=None, one=False, regex=False, **kwargs):
    """Extract log records from python's logging system.

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
        for key, value in kwargs.items():
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
        assert len(found) == count, f'Expected {count} records, got {len(found)}'
    if one:
        return found[0] if found else None
    return found


def assert_email_snapshot(snapshot, template, snapshot_filename):
    """Assert that an email matches a snapshot.

    This verifies that both the subject and the body match the snapshots.

    :param snapshot: The pytest snapshot fixture
    :param template: The email template module
    :param snapshot_filename: The filename for the snapshot
    """
    body = template.get_body()
    subject = template.get_subject()
    name, ext = os.path.splitext(snapshot_filename)
    snapshot_filename_subject = f'{name}.subject{ext}'
    __tracebackhide__ = True
    assert '\n' not in subject
    snapshot.assert_match(body, snapshot_filename)
    # we add a trailing linebreak so make manually editing the snapshot easier
    snapshot.assert_match(subject + '\n', snapshot_filename_subject)


def assert_json_snapshot(snapshot, obj, snapshot_filename):
    """Assert that a json object matches a snapshot.

    :param snapshot: The pytest snapshot fixture
    :param obj: The json object to compare
    :param snapshot_filename: The filename for the snapshot
    """
    __tracebackhide__ = True
    snapshot.assert_match(json.dumps(obj, indent=2, sort_keys=True), snapshot_filename)


def assert_yaml_snapshot(snapshot, obj, snapshot_filename, *, strip_dynamic_data=False):
    """Assert that a yaml object matches a snapshot.

    :param snapshot: The pytest snapshot fixture
    :param obj: The yaml object to compare
    :param snapshot_filename: The filename for the snapshot
    :param strip_dynamic_data: Whether to replace likely-dynamic data like IDs and
                               dates with placeholders
    """
    dumped = yaml.dump(obj)
    if strip_dynamic_data:
        dumped = remove_dynamic_data(dumped)
    __tracebackhide__ = True
    snapshot.assert_match(dumped, snapshot_filename)


def remove_dynamic_data(yaml_string):
    """Remove data that appears dynamic (IDs, dates) from a YAML string."""
    yaml_string = re.sub(r'(?<=_date: )(?!null$).+$', '<timestamp>', yaml_string, flags=re.MULTILINE)
    yaml_string = re.sub(r'(?<=_dt: )(?!null$).+$', '<timestamp>', yaml_string, flags=re.MULTILINE)
    yaml_string = re.sub(r'(?<=: )[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', '<uuid>',
                         yaml_string, flags=re.MULTILINE)
    yaml_string = re.sub(r'(?<=_id: )(?!null$).+$', '<id>', yaml_string, flags=re.MULTILINE)
    return re.sub(r'(?<=\bid: )(?!null$).+$', '<id>', yaml_string, flags=re.MULTILINE)
