# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date

import click
from dateutil.relativedelta import relativedelta

from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.statistics import calculate_rooms_occupancy
from indico.util.string import natural_sort_key
from indico.web.flask.app import make_app


def _main(location):
    yesterday = date.today() - relativedelta(days=1)
    past_month = yesterday - relativedelta(days=29)
    past_year = yesterday - relativedelta(years=1)

    query = Room.query
    if location:
        query = query.join(Location).filter(Location.name.in_(location))
    rooms = sorted(query, key=lambda r: natural_sort_key(r.location_name + r.full_name))

    print('Month\tYear\tPublic?\tRoom')
    for room in rooms:
        print('{:.2f}%\t{:.2f}%\t{}\t{}'.format(calculate_rooms_occupancy([room], past_month, yesterday) * 100,
                                                calculate_rooms_occupancy([room], past_year, yesterday) * 100,
                                                'Y' if room.is_public else 'N',
                                                room.full_name))


@click.command()
@click.option('--location', '-l', multiple=True, help='Filter by given location')
def main(location):
    with make_app().app_context():
        _main(location)


if __name__ == '__main__':
    main()
