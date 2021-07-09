# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from packaging.version import Version

from indico.modules.admin.notices import NoticeSeverity, SystemNotice, SystemNoticeCriteria
from indico.testing.util import extract_logs


@pytest.mark.parametrize(('criteria', 'expected'), (
    (SystemNoticeCriteria(python_version='< 3.10'), True),
    (SystemNoticeCriteria(python_version='< 3.10', indico_version='==3.0.1'), True),
    (SystemNoticeCriteria(python_version='< 3.10', indico_version='> 3'), True),
    (SystemNoticeCriteria(python_version='>=3.9.6', indico_version='< 3.0.2'), True),
    (SystemNoticeCriteria(python_version='>= 3.10'), False),
    (SystemNoticeCriteria(python_version='< 3.10', indico_version='!=3.0.1'), False),
    (SystemNoticeCriteria(python_version='< 3.10', indico_version='< 3'), False),
    (SystemNoticeCriteria(python_version='>=3.9.6', indico_version='> 3.0.2'), False),
))
def test_evaluate_notice(caplog, criteria, expected):
    versions = {
        'python_version': Version('3.9.6'),
        'postgres_version': Version('12.7'),
        'indico_version': Version('3.0.1')
    }
    notice = SystemNotice(id='test', message='testing', when=criteria, severity=NoticeSeverity.highlight)
    assert notice.evaluate(versions) == expected
    assert not extract_logs(caplog, required=False, name='indico.notices')


@pytest.mark.parametrize(('op', 'expected'), (
    ('==', True),
    ('!=', False),
    ('<', False),
    ('<=', True),
    ('>', False),
    ('>=', True),
))
@pytest.mark.parametrize('space', ('', ' '))
def test_evaluate_notice_all_ops(caplog, op, space, expected):
    versions = {
        'python_version': Version('3.14.15'),
        'postgres_version': Version('12.7'),
        'indico_version': Version('3.0.1')
    }
    criteria = SystemNoticeCriteria(python_version=f'{op}{space}3.14.15')
    notice = SystemNotice(id='test', message='testing', when=criteria, severity=NoticeSeverity.highlight)
    assert notice.evaluate(versions) == expected
    assert not extract_logs(caplog, required=False, name='indico.notices')


@pytest.mark.parametrize(('criterion', 'message'), (
    ('!= 1.2.3foo', 'Invalid version in test: python_version != 1.2.3foo'),
    ('! foo', 'Invalid criterion in test: python_version ! foo'),
))
def test_evaluate_notice_invalid(caplog, criterion, message):
    versions = {
        'python_version': Version('3.14.15'),
        'postgres_version': Version('12.7'),
        'indico_version': Version('3.0.1')
    }
    criteria = SystemNoticeCriteria(python_version=criterion)
    notice = SystemNotice(id='test', message='testing', when=criteria, severity=NoticeSeverity.highlight)
    assert not notice.evaluate(versions)
    assert extract_logs(caplog, one=True, name='indico.notices').message == message


def test_render_message():
    versions = {
        'python_version': Version('3.9.6'),
        'postgres_version': Version('12.7'),
        'indico_version': Version('3.0.1')
    }
    message = '{python_version} **{postgres_version}** {indico_version}'
    notice = SystemNotice(id='test', message=message, when=SystemNoticeCriteria(), severity=NoticeSeverity.highlight)
    assert str(notice.render_message(versions)) == '<p>3.9.6 <strong>12.7</strong> 3.0.1</p>'
