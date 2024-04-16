# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import logging
import re
from importlib.metadata import entry_points
from urllib.parse import parse_qs, urlsplit, urlunsplit

import requests
import sentry_sdk
from flask import request
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger
from sentry_sdk.integrations.pure_eval import PureEvalIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from werkzeug.datastructures import MultiDict

import indico
from indico.core.config import config
from indico.core.logger import Logger
from indico.util.i18n import set_best_lang


logger = Logger.get('sentry')


def init_sentry(app):
    plugin_packages = {
        ep.value.split(':')[0].split('.')[0]
        for ep in entry_points(group='indico.plugins')
    }

    ignore_logger('indico.flask')
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        release=indico.__version__,
        send_default_pii=True,
        attach_stacktrace=True,
        propagate_traces=False,
        in_app_include=({'indico'} | plugin_packages),
        integrations=[
            PureEvalIntegration(),
            RedisIntegration(),
            FlaskIntegration(transaction_style='url'),
            LoggingIntegration(event_level=getattr(logging, config.SENTRY_LOGGING_LEVEL))
        ],
        _experiments={'record_sql_params': True}
    )

    app.before_request(_set_request_info)


def _set_request_info():
    sentry_sdk.set_extra('Endpoint', str(request.url_rule.endpoint) if request.url_rule else None)
    sentry_sdk.set_extra('Request ID', request.id)
    sentry_sdk.set_tag('locale', set_best_lang())


def submit_user_feedback(error_data, email, comment):
    if not config.SENTRY_DSN:
        return

    # get rid of credentials or query string in case they are present in the DSN
    dsn = re.sub(r':[^@/]+(?=@)', '', config.SENTRY_DSN)
    url = urlsplit(dsn)
    dsn = urlunsplit(url._replace(query=''))
    query = MultiDict(parse_qs(url.query))
    verify = query.get('ca_certs', True)
    hostname = url.netloc.rpartition('@')[2]  # host w/o credentials
    url = urlunsplit(url._replace(path='/api/embed/error-page/', netloc=hostname, query=''))
    url = _resolve_redirects(url, verify)
    user_data = error_data['request_info']['user'] or {'name': 'Anonymous', 'email': config.NO_REPLY_EMAIL}
    try:
        rv = requests.post(
            url,
            params={
                'dsn': dsn,
                'eventId': error_data['sentry_event_id']
            },
            data={
                'name': user_data['name'],
                'email': email or user_data['email'],
                'comments': comment
            },
            headers={'Origin': config.BASE_URL},
            verify=verify,
        )
        rv.raise_for_status()
    except Exception:
        # don't bother users if this fails!
        logger.exception('Could not submit user feedback')


def _resolve_redirects(url, verify):
    try:
        return requests.head(url, allow_redirects=True, verify=verify).url
    except Exception:
        logger.exception('Could not resolve redirects')
        return url
