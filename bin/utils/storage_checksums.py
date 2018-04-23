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
            .filter(model.md5 == '', model.storage_file_id.isnot(None))
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
    models = {model: total for model, total in models.iteritems() if total}
    labels = {model: cformat('Processing %{blue!}{}%{reset} (%{cyan}{}%{reset} rows)').format(model.__name__, total)
              for model, total in models.iteritems()}
    max_length = max(len(x) for x in labels.itervalues())
    labels = {model: label.ljust(max_length) for model, label in labels.iteritems()}
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
