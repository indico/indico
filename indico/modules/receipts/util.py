# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses
import typing as t
from io import BytesIO
from operator import attrgetter
from urllib.parse import urlparse

from flask import g
from jinja2 import TemplateRuntimeError, Undefined
from jinja2.exceptions import SecurityError, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup
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


def compile_jinja_code(code: str, use_stack: bool = False, **fields) -> str:
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
            **fields,
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


def get_useful_registration_data(reg_form: RegistrationForm, registration: Registration):
    """Collect a series of useful data about a registration and make it available as a dict.

    :param registration: a `Registration` object
    :return: a `dict` containing useful fields for templating
    """
    fields = []
    for field in sorted(reg_form.active_fields, key=attrgetter('parent.position', 'position')):
        field_data = field.current_data.versioned_data
        data = registration.data_by_field.get(field.id)
        value = data.data if data else None
        fields.append({
            'title': field.title,
            'section_title': field.parent.title,
            'input_type': field.input_type,
            'value': value,
            'friendly_value': data.get_friendly_data(for_humans=True),
            'field_data': field_data,
            'actual_price': data.price if data else None
        })

    return {
        'personal_data': registration.get_personal_data(),
        'fields': fields,
        'base_price': registration.base_price,
        'total_price': registration.price,
        'currency': reg_form.currency,
        'formatted_price': registration.render_price()
    }
