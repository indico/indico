# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import typing as t
from io import BytesIO

from flask import g
from jinja2 import Undefined
from jinja2.sandbox import SandboxedEnvironment
from weasyprint import CSS, HTML, default_url_fetcher

from indico.modules.categories.models.categories import Category
from indico.modules.events.models.events import Event
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.receipts.models.templates import ReceiptTemplate


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


class SilentUndefined(Undefined):
    __slots__ = ()

    def _fail_with_undefined_error(self, *args, **kwargs):
        g.template_stack[-1].undefined.add(self._undefined_name)
        return f'<span class="error">Undefined: <span class="var-name">{self._undefined_name}</span></span>'


def get_all_templates(obj: t.Union[Event, Category]) -> set[ReceiptTemplate]:
    """Get all templates usable by an event/category."""
    category = obj.category if isinstance(obj, Event) else obj
    return set(ReceiptTemplate.query.filter(ReceiptTemplate.category_id.in_(categ['id'] for categ in category.chain)))


def get_inherited_templates(obj: t.Union[Event, Category]) -> set[ReceiptTemplate]:
    """Get all templates inherited by a given event/category."""
    return get_all_templates(obj) - set(obj.receipt_templates)


def compile_jinja_code(code: str, use_stack: bool = False, **fields) -> str:
    """Compile Jinja template of receipt in a sandboxed environment."""
    env = SandboxedEnvironment(undefined=SilentUndefined) if use_stack else SandboxedEnvironment()
    return env.from_string(code).render(**fields)


def sandboxed_url_fetcher(event: Event, **kwargs) -> t.Callable[[str], dict]:
    """Fetch also "event-local" URLs.

    More info on fetchers: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#url-fetchers
    """
    def _fetcher(url: str) -> dict:
        if url == 'event://logo':
            return {
                'mime_type': event.logo_metadata['content_type'],
                'string': event.logo
            }
        return default_url_fetcher(url)
    return _fetcher


def create_pdf(event: Event, html_sources: t.List[str], css: str) -> BytesIO:
    """Create a PDF based on the given HTML sources.

    :param event: The `Event` the PDF relates to
    :param html_sources: list of HTML pages (source) which will be rendered into the final document
    :param css: CSS stylesheet to include
    :return: a the rendered PDF blob
    """
    css = CSS(string=f'{css}{DEFAULT_CSS}')
    documents = [
        HTML(string=source, url_fetcher=sandboxed_url_fetcher(event)).render(stylesheets=(css,))
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
    for field in reg_form.active_fields:
        field_data = field.current_data.versioned_data
        data = registration.data_by_field.get(field.id)
        value = data.data if data else None
        fields.append({
            'title': field.title,
            'value': value,
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
