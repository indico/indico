# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import itemgetter

import click
from sqlalchemy import inspect
from sqlalchemy.orm import lazyload, load_only
from sqlalchemy.sql.elements import Tuple

from indico.core.db import db
from indico.core.storage import StoredFileMixin
from indico.modules.events.static.models.static import StaticSite, StaticSiteState
from indico.util.console import cformat
from indico.util.fs import get_file_checksum
from indico.web.flask.app import make_app


SPECIAL_FILTERS = {
    StaticSite: {'state': StaticSiteState.success}
}


def make_query(model):
    return (model.query
            .filter(model.md5 == '', model.storage_file_id.isnot(None))  # noqa: PLC1901
            .filter_by(**SPECIAL_FILTERS.get(model, {}))
            .options(lazyload('*'), load_only('storage_backend', 'storage_file_id', 'md5')))


def query_chunked(model, chunk_size):
    pks = inspect(model).primary_key
    query = base_query = make_query(model).order_by(*pks)
    while True:
        row = None
        for row in query.limit(chunk_size):
            yield row
        db.session.commit()
        if row is None:
            # no rows in the query
            break
        query = base_query.filter(Tuple(*pks) > inspect(row).identity)


def main():
    models = {model: make_query(model).count() for model in StoredFileMixin.__subclasses__()}
    models = {model: total for model, total in models.items() if total}
    labels = {model: cformat('Processing %{blue!}{}%{reset} (%{cyan}{}%{reset} rows)').format(model.__name__, total)
              for model, total in models.items()}
    max_length = max(len(x) for x in labels.values())
    labels = {model: label.ljust(max_length) for model, label in labels.items()}
    for model, total in sorted(models.items(), key=itemgetter(1)):
        with click.progressbar(query_chunked(model, 100), length=total, label=labels[model],
                               show_percent=True, show_pos=True) as objects:
            for obj in objects:
                try:
                    with obj.open() as f:
                        checksum = get_file_checksum(f)
                except Exception as exc:
                    click.echo(cformat('\n%{red!}Could not open %{reset}%{yellow}{}%{red!}: %{reset}%{yellow!}{}')
                               .format(obj, exc))
                else:
                    obj.md5 = checksum


@click.command()
def cli():
    with make_app().app_context():
        main()


if __name__ == '__main__':
    cli()
