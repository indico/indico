# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses
import operator
import platform
import re
from enum import StrEnum, auto

import requests
import yaml
from celery.schedules import crontab
from flask import session
from markupsafe import Markup
from marshmallow import EXCLUDE, ValidationError, fields, post_load
from marshmallow_dataclass import dataclass
from packaging.version import InvalidVersion, Version

import indico
from indico.core.cache import make_scoped_cache
from indico.core.celery import celery
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import get_postgres_version
from indico.core.logger import Logger
from indico.core.marshmallow import mm
from indico.util.caching import memoize_request
from indico.util.string import render_markdown
from indico.web.flask.templating import template_hook


logger = Logger.get('notices')
notices_cache = make_scoped_cache('notices')


class NoticeSeverity(StrEnum):
    highlight = auto()
    warning = auto()
    error = auto()


@dataclass(frozen=True)
class SystemNoticeCriteria:
    python_version: str | None = None
    postgres_version: str | None = None
    indico_version: str | None = None


@dataclass(frozen=True)
class SystemNotice:
    class Meta:
        unknown = EXCLUDE

    id: str
    message: str
    when: SystemNoticeCriteria
    severity: NoticeSeverity
    announcement_bar: bool = False

    def evaluate(self, versions):
        ops = {
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
        }
        for key, value in dataclasses.asdict(self.when).items():
            if value is None:
                continue
            if not (match := re.match(fr'^(?P<op>{"|".join(map(re.escape, ops))})\s*(?P<val>[0-9]\S*)$', value)):
                logger.warning('Invalid criterion in %s: %s %s', self.id, key, value)
                return False
            current_version = versions[key]
            try:
                expected_version = Version(match.group('val'))
            except InvalidVersion:
                logger.warning('Invalid version in %s: %s %s', self.id, key, value)
                return False
            if not ops[match.group('op')](current_version, expected_version):
                return False
        return True

    def render_message(self, versions):
        message = self.message
        for key, value in versions.items():
            message = message.replace(f'{{{key}}}', str(value))
        return Markup(render_markdown(message))


class SystemNoticesSchema(mm.Schema):
    class Meta:
        unknown = EXCLUDE

    notices = fields.List(fields.Nested(SystemNotice.Schema), required=True)

    @post_load
    def _unwrap(self, data, **kwargs):
        return data['notices']


def load_notices():
    if not config.SYSTEM_NOTICES_URL:
        return None
    try:
        resp = requests.get(config.SYSTEM_NOTICES_URL)
        resp.raise_for_status()
    except requests.RequestException:
        logger.exception('Could not fetch notices')
        return None
    try:
        data = yaml.safe_load(resp.content)
        return SystemNoticesSchema().load(data)
    except (yaml.YAMLError, ValidationError):
        logger.exception('Could not parse notices')
        return None


@memoize_request
def _get_versions():
    return {
        'postgres_version': Version(get_postgres_version()),
        'python_version': Version(platform.python_version()),
        'indico_version': Version(indico.__version__),
    }


def _get_notices(*, announcement_bar: bool):
    if not config.SYSTEM_NOTICES_URL or not session.user or not session.user.is_admin:
        return []
    if not (notices := notices_cache.get('notices')):
        return []
    return [n for n in notices if n.announcement_bar == announcement_bar and n.evaluate(_get_versions())]


@template_hook('global-announcement', priority=-90, markup=False)
def _inject_system_notice_header(**kwargs):
    for notice in _get_notices(announcement_bar=True):
        yield notice.severity.value, notice.render_message(_get_versions()), True


@template_hook('admin-system-notices', priority=-90, markup=False)
def _inject_system_notice_admin(**kwargs):
    for notice in _get_notices(announcement_bar=False):
        yield notice.severity.value, notice.render_message(_get_versions())


@celery.periodic_task(name='update_system_notices', run_every=crontab(minute='30', hour='3'))
def update_system_notices():
    notices = load_notices()
    if notices is not None:
        notices_cache.set('notices', notices)
        db.session.commit()
