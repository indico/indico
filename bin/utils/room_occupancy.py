# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
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
from indico.web.flask.app import make_app


def _main(location):
    yesterday = date.today() - relativedelta(days=1)
    past_month = yesterday - relativedelta(days=29)
    past_year = yesterday - relativedelta(years=1)

    if not location:
        rooms = Room.find_all()
    else:
        rooms = Room.find_all(Location.name.in_(location), _join=Location)

    print('Month\tYear\tPublic?\tRoom')
    for room in rooms:
        print('{2:.2f}%\t{3:.2f}%\t{1}\t{0}'.format(room.full_name,
                                                    "Y" if room.is_public else "N",
                                                    calculate_rooms_occupancy([room], past_month, yesterday) * 100,
                                                    calculate_rooms_occupancy([room], past_year, yesterday) * 100))


@click.command()
@click.option('--location', '-l', multiple=True, help="Filter by given location")
def main(location):
    with make_app().app_context():
        _main(location)


if __name__ == '__main__':
    main()
