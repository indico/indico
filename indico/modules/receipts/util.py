# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses
import typing as t
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import yaml
from flask import current_app, g
from jinja2 import TemplateRuntimeError, Undefined
from jinja2.exceptions import SecurityError, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer
from sqlalchemy.sql import or_
from weasyprint import CSS, HTML, default_url_fetcher
from webargs.flaskparser import abort
from werkzeug.exceptions import UnprocessableEntity

from indico.core.config import config
from indico.core.logger import Logger
from indico.modules.categories.models.categories import Category
from indico.modules.events.models.events import Event
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.receipts.models.files import ReceiptFile
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.modules.receipts.settings import receipts_settings
from indico.util.date_time import format_date, format_datetime, format_time, now_utc
from indico.util.i18n import _
from indico.util.iterables import materialize_iterable


logger = Logger.get('receipts')

DEFAULT_CSS = '''
.error {
    border: 1px solid red;
    color: red;
    padding: 0.2em;
}

.error .var-name {
    color: white;
    background-color: red;
    padding: 0.1em;
    margin: 0.1em;
}
'''


def can_user_manage_receipt_templates(user):
    if not user:
        return False
    if user.is_admin:
        return True
    return receipts_settings.acls.contains_user('authorized_users', user)


@dataclasses.dataclass
class TemplateStackEntry:
    registration: Registration
    undefined: set[str] = dataclasses.field(default_factory=set)


class SilentUndefined(Undefined):
    __slots__ = ()

    def _fail_with_undefined_error(self, *args, **kwargs):
        g.template_stack[-1].undefined.add(self._undefined_name)
        return (Markup('<span class="error">Undefined: <span class="var-name">{}</span></span>')
                .format(self._undefined_name))

    # StrictUndefined behavior but with our custom failure method
    __iter__ = __str__ = __len__ = _fail_with_undefined_error
    __eq__ = __ne__ = __bool__ = __hash__ = _fail_with_undefined_error
    __contains__ = _fail_with_undefined_error
    # Make sure markupsafe doesn't escape our Markup object
    __html__ = _fail_with_undefined_error


def get_all_templates(obj: t.Union[Event, Category]) -> set[ReceiptTemplate]:
    """Get all templates usable by an event/category."""
    category = obj.category if isinstance(obj, Event) else obj
    return set(ReceiptTemplate.query.filter(~ReceiptTemplate.is_deleted,
                                            ReceiptTemplate.category_id.in_(categ['id'] for categ in category.chain)))


def has_any_templates(event: Event) -> bool:
    """Check if any receipt templates are available for the event."""
    return (ReceiptTemplate.query
            .filter(~ReceiptTemplate.is_deleted,
                    or_(ReceiptTemplate.category_id.in_(categ['id'] for categ in event.category.chain),
                        ReceiptTemplate.event == event))
            .has_rows())


def has_any_receipts(regform: RegistrationForm) -> bool:
    """Check if any receipts have been generated available for the regform."""
    return (ReceiptFile.query
            .filter(ReceiptFile.registration.has(is_deleted=False, registration_form=regform),
                    ~ReceiptFile.is_deleted)
            .has_rows())


def get_inherited_templates(obj: t.Union[Event, Category]) -> set[ReceiptTemplate]:
    """Get all templates inherited by a given event/category."""
    return get_all_templates(obj) - set(obj.receipt_templates)


def compile_jinja_code(code: str, template_context: dict, *, use_stack: bool = False) -> str:
    """Compile Jinja template of receipt in a sandboxed environment."""
    try:
        undefined_config = {'undefined': SilentUndefined} if use_stack else {}
        env = SandboxedEnvironment(**undefined_config, autoescape=True)
        env.filters.update({
            'format_date': format_date,
            'format_datetime': format_datetime,
            'format_time': format_time,
        })
        return env.from_string(code).render(
            **template_context,
            now_utc=now_utc
        )
    except (TemplateSyntaxError, TemplateRuntimeError, SecurityError, LookupError, TypeError, ValueError) as e:
        raise UnprocessableEntity(e)


def sandboxed_url_fetcher(event: Event, allow_event_logo: bool = False) -> t.Callable[[str], dict]:
    """Fetch also "event-local" URLs.

    More info on fetchers: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#url-fetchers
    """
    allow_external_urls = receipts_settings.get('allow_external_urls')

    def _fetcher(url: str) -> dict:
        if allow_event_logo and url == 'event://logo':
            return {
                'mime_type': event.logo_metadata['content_type'],
                'string': event.logo
            }

        # Make sure people don't do anything funny...
        url_data = urlparse(url)
        if url_data.scheme not in {'http', 'https'}:
            if url_data.scheme == 'file':
                logger.warning('Attempted to use local file URL %s in a document template', url)
            raise ValueError('Invalid URL scheme')

        if not allow_external_urls and not url.startswith(config.BASE_URL):
            raise ValueError('External URLs not allowed')

        return default_url_fetcher(url)

    return _fetcher


def create_pdf(event: Event, html_sources: list[str], css: str) -> BytesIO:
    """Create a PDF based on the given HTML sources.

    :param event: The `Event` the PDF relates to
    :param html_sources: list of HTML pages (source) which will be rendered into the final document
    :param css: CSS stylesheet to include
    :return: a the rendered PDF blob
    """
    css_url_fetcher = sandboxed_url_fetcher(event)
    html_url_fetcher = sandboxed_url_fetcher(event, allow_event_logo=True)
    try:
        css = CSS(string=f'{css}{DEFAULT_CSS}', url_fetcher=css_url_fetcher)
    except IndexError:
        # error happens when parsing `flex: ;` in the stylesheet
        # https://github.com/Kozea/WeasyPrint/issues/2012
        abort(422, messages={'css': [_('Could not parse stylesheet')]})
    documents = [
        HTML(string=source, url_fetcher=html_url_fetcher).render(stylesheets=(css,))
        for source in html_sources
    ]
    all_pages = [p for doc in documents for p in doc.pages]
    f = BytesIO()
    documents[0].copy(all_pages).write_pdf(f)
    f.seek(0)
    return f


def get_safe_template_context(event: Event, registration: Registration, custom_fields: dict) -> dict:
    """Get a safe version of the data needed to render a document template.

    This uses just primitive Python types (and datetime objects) and, in particular,
    avoids passing any database objects which would make it trivial to make changes
    to the database when simply rendering a template.
    """
    from indico.modules.receipts.schemas import TemplateDataSchema
    tds = TemplateDataSchema()
    dumped = tds.dump({
        'event': event,
        'registration': registration,
        'custom_fields': custom_fields,
    })
    # This round-trip through marshmallow loads it back to a plain dict while converting
    # e.g. date strings back to actual datetime objects
    return tds.load(dumped)


def _get_default_value(field):
    if field['type'] == 'dropdown' and 'default' in field['attributes']:
        return field['attributes']['options'][field['attributes']['default']]
    elif field['type'] == 'checkbox':
        return field['attributes'].get('value', False)
    return field['attributes'].get('value', '')


def get_dummy_preview_data(custom_fields: dict) -> dict:
    """Get dummy preview data for rendering a document template.

    Most document templates are written inthe context of a category, so it is not
    possible to use real event/registration data for previewing it. This function
    serializes dummy data that can be used instead.
    """
    from indico.modules.receipts.schemas import TemplateDataSchema
    dummy_file = Path(current_app.root_path) / 'modules' / 'receipts' / 'dummy_data.yaml'
    dummy_data = yaml.safe_load(dummy_file.read_text())
    return TemplateDataSchema().load({
        **dummy_data,
        'custom_fields': {f['name']: _get_default_value(f) for f in custom_fields},
    })


def _render_placeholder_value(value):
    if isinstance(value, datetime):
        return f'<{value}> (Python datetime object)'
    return highlight(repr(value), PythonLexer(), HtmlFormatter(noclasses=True))


@materialize_iterable()
def _get_preview_placeholders(value: t.Any, _name: str = ''):
    if isinstance(value, dict):
        for k, v in value.items():
            prefix = f'{_name}.' if _name else ''
            if prefix.startswith('registration.field_data[') and k in ('config', 'raw_value'):
                # don't descend into config and raw value of a field
                yield f'{prefix}{k}', _render_placeholder_value(v)
            else:
                yield from _get_preview_placeholders(v, f'{prefix}{k}')
    elif isinstance(value, list):
        if _name == 'registration.field_data':
            # separate placeholders for each field
            for i, v in enumerate(value):
                yield from _get_preview_placeholders(v, f'{_name}[{i}]')
        else:
            yield _name, _render_placeholder_value(value)
    else:
        yield _name, _render_placeholder_value(value)


def get_preview_placeholders(value):
    """Get a flat list of placeholders from the template context."""
    placeholders = _get_preview_placeholders(value)
    placeholders.sort(key=lambda x: (
        not x[0].startswith('custom_fields.'),
        not x[0].startswith('event.'),
        x[0].startswith('registration.field_data['),
    ))
    return placeholders
