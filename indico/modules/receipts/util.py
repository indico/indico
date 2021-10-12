# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import typing as t
from io import BytesIO

from jinja2.sandbox import SandboxedEnvironment
from weasyprint import CSS, HTML, default_url_fetcher

from indico.modules.categories.models.categories import Category
from indico.modules.events.models.events import Event
from indico.modules.receipts.models.templates import ReceiptTemplate


def get_all_templates(obj: t.Union[Event, Category]) -> set[ReceiptTemplate]:
    """Get all templates usable by an event/category."""
    category = obj.category if isinstance(obj, Event) else obj
    return set(ReceiptTemplate.query.filter(ReceiptTemplate.category_id.in_(categ['id'] for categ in category.chain)))


def get_inherited_templates(obj: t.Union[Event, Category]) -> set[ReceiptTemplate]:
    """Get all templates inherited by a given event/category."""
    return get_all_templates(obj) - set(obj.receipt_templates)


def compile_jinja_code(code: str, **fields) -> str:
    """Compile Jinja template of receipt in a sandboxed environment."""
    env = SandboxedEnvironment()
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


def create_pdf(event: Event, html_code: str, css: str) -> BytesIO:
    """Create a PDF based on the given template and data."""
    html = HTML(string=html_code, url_fetcher=sandboxed_url_fetcher(event))
    f = BytesIO()
    css = CSS(string=css)
    html.write_pdf(f, stylesheets=(css,))
    f.seek(0)
    return f
