# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import division, unicode_literals

from collections import defaultdict, namedtuple
from itertools import chain, groupby

from indico.modules.events.registration.models.registrations import RegistrationData
from indico.util.date_time import now_utc
from indico.util.i18n import _


class StatsBase(object):
    def __init__(self, title, subtitle, type, **kwargs):
        """Base class for registration form statistics

        :param title: str -- the title for the stats box
        :param subtitle: str -- the subtitle for the stats box
        :param type: str -- the type used in Jinja to display the stats
        """
        super(StatsBase, self).__init__(**kwargs)
        self.title = title
        self.subtitle = subtitle
        self.type = type

    @property
    def is_currency_shown(self):
        return False


class Cell(namedtuple('Cell', ['type', 'data', 'colspan', 'classes', 'qtip'])):
    """Hold data and type for a cell of a stats table"""

    _type_defaults = {
        'str': '',
        'progress-stacked': [[0], '0'],
        'progress': (0, '0'),
        'currency': 0,
        'icon': 'warning'
    }

    def __new__(cls, type='default', data=None, colspan=1, classes=None, qtip=None):
        """
        The table below indicates the valid types and expected data.

        +--------------------+-----------------------------------------+
        | type               | data                                    |
        +====================+=========================================+
        | `str`              | `str` -- string value                   |
        +--------------------+-----------------------------------------+
        | `progress`         | `(int, str)` -- a tuple with the        |
        |                    | progress (a value between 0 and 1) and  |
        |                    | a label                                 |
        +--------------------+-----------------------------------------+
        | `progress-stacked` | `([int], str)` -- a tuple with a list   |
        |                    | of progresses (values which must sum up |
        |                    | to 1) and a label                       |
        +--------------------+-----------------------------------------+
        | `currency`         | `float` -- numeric value                |
        +--------------------+-----------------------------------------+
        | `icon`             | `str` -- icon name from `_icons.scss`   |
        +--------------------+-----------------------------------------+
        | `default`          | `None` -- renders a default cell with   |
        |                    | an `&mdash;` (use `Cell(type='str')`    |
        |                    | for an empty cell)                      |
        +--------------------+-----------------------------------------+

        :param type: str -- The type of data in the cell
        :param data: The data for the cell
        :param colspan: int -- HTML colspan value for the cell
        :param classes: [str] -- HTML classes to apply to the cell
        :param qtip: str -- content for qtip
        """
        if classes is None:
            classes = []
        if data is None:
            data = Cell._type_defaults.get(type, None)
        return super(Cell, cls).__new__(cls, type, data, colspan, classes, qtip)


class DataItem(namedtuple('DataItem', ['regs', 'attendance', 'capacity', 'billable', 'cancelled', 'price',
                                       'fixed_price', 'paid', 'paid_amount', 'unpaid', 'unpaid_amount'])):
    def __new__(cls, regs=0, attendance=0, capacity=0, billable=False, cancelled=False, price=0, fixed_price=False,
                paid=0, paid_amount=0, unpaid=0, unpaid_amount=0):
        """
        Holds the aggregation of some data, intended for stats tables as
        a aggregation from which to generate cells.

        :param regs: int -- number of registrant
        :param attendance: int -- number of people attending
        :param capacity: int -- maximum number of people allowed to
                         attend (`0` if unlimited)
        :param billable: bool -- whether the item is billable to the or
                         not
        :param cancelled: bool -- whether the item is cancelled or not
        :param price: str -- the price of the item
        :param fixed_price: bool -- `True` if the price is per
                            registrant, `False` if accompanying guests
                            must pay as well.
        :param paid: int -- number of registrants who paid
        :param paid_amount: float -- amount already paid by registrants
        :param unpaid: int -- number of registrants who haven't paid
        :param unpaid_amount: float -- amount not already paid by
                              registrants
        """
        return super(DataItem, cls).__new__(cls, regs, attendance, capacity, billable, cancelled, price, fixed_price,
                                            paid, paid_amount, unpaid, unpaid_amount)


class FieldStats(object):
    """Holds stats for a registration form field"""

    def __init__(self, field, **kwargs):
        kwargs.setdefault('type', 'table')
        super(FieldStats, self).__init__(**kwargs)
        self._field = field
        self._regitems = self._get_registration_data(field)
        self._choices = self._get_choices(field)
        self._data, self._show_billing_info = self._build_data()

    @property
    def is_currency_shown(self):
        return self._show_billing_info

    def _get_choices(self, field):
        return {choice['id']: choice for choice in field.current_data.versioned_data['choices']}

    def _get_registration_data(self, field):
        registration_ids = [r.id for r in field.registration_form.active_registrations]
        field_data_ids = [data.id for data in field.data_versions]
        return RegistrationData.find_all(RegistrationData.registration_id.in_(registration_ids),
                                         RegistrationData.field_data_id.in_(field_data_ids),
                                         RegistrationData.data != {})

    def _build_data(self):
        """Build data from registration data and field choices

        :returns: (dict, bool) -- the data and a boolean to indicate
                  whether the data contains billing information or not.
        """
        choices = defaultdict(dict)
        data = defaultdict(list)
        regitems = sorted(self._regitems, key=self._build_key)
        for k, regitems in groupby((regitem for regitem in regitems if regitem.price), key=self._build_key):
            choices['billed'][k] = self._build_regitems_data(k, list(regitems))
        for k, regitems in groupby((regitem for regitem in regitems if not regitem.price), key=self._build_key):
            choices['not_billed'][k] = self._build_regitems_data(k, list(regitems))
        for item in self._choices.itervalues():
            key = 'billed' if item['price'] else 'not_billed'
            choices[key].setdefault(self._build_key(item), self._build_choice_data(item))
        for key, choice in chain(choices['billed'].iteritems(), choices['not_billed'].iteritems()):
            data[key[:2]].append(choice)
        return data, bool(choices['billed'])

    def get_table(self):
        """Returns a table containing the stats for each item.

        :return: dict -- A table with a list of head cells
                 (key: `'head'`) and a list of rows (key: `'rows'`)
                 where each row is a list of cells.
        """
        table = defaultdict(list)
        table['head'] = self._get_table_head()
        for (name, id), data_items in sorted(self._data.iteritems()):
            total_regs = sum(detail.regs for detail in data_items)
            table['rows'].append(('single-row' if len(data_items) == 1 else 'header-row',
                                 self._get_main_row_cells(data_items, name, total_regs) +
                                 self._get_billing_cells(data_items)))
            if len(data_items) == 1:
                continue
            table['rows'].extend(('sub-row',
                                 self._get_sub_row_cells(data_item, total_regs) +
                                 self._get_billing_details_cells(data_item))
                                 for data_item in data_items)
        return table

    def _get_billing_cells(self, data_items):
        """Return cells with billing information from data items

        :params data_items: [DataItem] -- Data items containing billing info
        :returns: [Cell] -- Cells containing billing information.
        """
        if not self._show_billing_info:
            return []
        if len(data_items) == 1:
            return self._get_billing_details_cells(data_items[0])
        paid = sum(detail.paid for detail in data_items if detail.billable)
        paid_amount = sum(detail.paid_amount for detail in data_items if detail.billable)
        unpaid = sum(detail.unpaid for detail in data_items if detail.billable)
        unpaid_amount = sum(detail.unpaid_amount for detail in data_items if detail.billable)
        total = paid + unpaid
        total_amount = paid_amount + unpaid_amount
        progress = [[paid / total, unpaid / total], '{} / {}'.format(paid, total)] if total else None
        return [Cell(),
                Cell(type='progress-stacked', data=progress, classes=['paid-unpaid-progress']),
                Cell(type='currency', data=paid_amount, classes=['paid-amount', 'stick-left']),
                Cell(type='currency', data=unpaid_amount, classes=['unpaid-amount', 'stick-right']),
                Cell(type='currency', data=total_amount)]

    def _get_billing_details_cells(self, detail):
        """Return cells with detailed billing information

        :params item_details: DataItem -- Data items containing billing info
        :returns: [Cell] -- Cells containing billing information.
        """
        if not self._show_billing_info:
            return []
        if not detail.billable:
            return [Cell(type='currency', data=0),
                    Cell(),
                    Cell(type='currency', data=0, classes=['paid-amount', 'stick-left']),
                    Cell(type='currency', data=0, classes=['unpaid-amount', 'stick-right']),
                    Cell(type='currency', data=0)]
        progress = [[detail.paid / detail.regs, detail.unpaid / detail.regs],
                    '{0.paid} / {0.regs}'.format(detail)] if detail.regs else None
        return [Cell(type='currency', data=float(detail.price)),
                Cell(type='progress-stacked', data=progress, classes=['paid-unpaid-progress']),
                Cell(type='currency', data=detail.paid_amount, classes=['paid-amount', 'stick-left']),
                Cell(type='currency', data=detail.unpaid_amount, classes=['unpaid-amount', 'stick-right']),
                Cell(type='currency', data=detail.paid_amount + detail.unpaid_amount)]

    def _build_key(self, item):
        """Return the key to sort and group field choices

        It must include the caption and the id of the item as well as other
        billing information by which to aggregate.

        :param item: the item from which to derive a key.
        :returns: tuple -- tuple defining the key.
        """
        raise NotImplementedError

    def _build_regitems_data(self, key, regitems):
        """Return a `DataItem` aggregating data from registration items

        :param regitems: list -- list of registrations items to be aggregated
        :returns: DataItem -- the data aggregation
        """
        raise NotImplementedError

    def _build_choice_data(self, item):
        """
        Returns a `DataItem` containing the aggregation of an item which
        is billed to the registrants.

        :param item: list -- item to be aggregated
        :returns: DataItem -- the aggregation of the `item`
        """
        raise NotImplementedError

    def _get_table_head(self):
        """
        Returns a list of `Cell` corresponding to the headers of a the
        table.

        :returns: [Cell] -- the headers of the table.
        """
        raise NotImplementedError

    def _get_main_row_cells(self, item_details, choice_caption, total_regs):
        """
        Returns the cells of the main (header or single) row of the table.

        Each `item` has a main row. The row is a list of `Cell` which matches
        the table head.

        :param item_details: [DataItem] -- list of aggregations for the
                             item
        :param choice_caption: str -- the item's name
        :param total_regs: int -- the number of registrations for the item

        :returns: [Cell] -- the list of cells constituting the row.
        """
        raise NotImplementedError

    def _get_sub_row_cells(self, details, total_regs):
        """
        Returns the cells of the sub row of the table.

        An `item` can have a sub row. The row is a list of `Cell` which
        matches the table head.

        :param details: DataItem -- aggregation for the item
        :param total_regs: int -- the number of registrations for the item

        :returns: [Cell] -- the list of cells constituting the row.
        """
        raise NotImplementedError


class OverviewStats(StatsBase):
    """Generic stats for a registration form"""

    def __init__(self, regform):
        super(OverviewStats, self).__init__(title=_("Overview"), subtitle="", type='overview')
        self.regform = regform
        self.registrations = regform.active_registrations
        self.countries, self.num_countries = self._get_countries()
        self.availability = self._get_availibility()
        self.days_left = max((self.regform.end_dt - now_utc()).days, 0) if self.regform.end_dt else 0

    def _get_countries(self):
        countries = defaultdict(int)
        for country, regs in groupby(self.registrations, lambda x: x.get_personal_data().get('country')):
            if country is None:
                continue
            countries[country] += sum(1 for x in regs)
        if not countries:
            return [], 0
        # Sort by highest number of people per country then alphabetically per countries' name
        countries = sorted(((val, name) for name, val in countries.iteritems()),
                           key=lambda x: (-x[0], x[1]), reverse=True)
        return countries[-15:], len(countries)

    def _get_availibility(self):
        limit = self.regform.registration_limit
        if not limit or self.regform.limit_reached:
            return (0, 0, 0)
        return (len(self.registrations), limit, len(self.registrations) / limit)


class AccommodationStats(FieldStats, StatsBase):
    def __init__(self, field):
        super(AccommodationStats, self).__init__(title=_("Accommodation"), subtitle=field.title, field=field)
        self.has_capacity = any(detail.capacity for acco_details in self._data.itervalues()
                                for detail in acco_details if detail.capacity)

    def _get_occupancy(self, acco_details):
        if not self.has_capacity:
            return []
        capacity = max(d.capacity for d in acco_details)
        if not capacity:
            return [Cell()]
        regs = sum(d.regs for d in acco_details)
        return [Cell(type='progress', data=(regs / capacity, '{} / {}'.format(regs, capacity)))]

    def _get_occupancy_details(self, details):
        if not self.has_capacity:
            return []
        if not details.capacity:
            return [Cell()]
        return [Cell(type='progress',
                     data=(details.regs / details.capacity, '{0.regs} / {0.capacity}'.format(details)))]

    def _build_key(self, obj):
        choice_id = obj.data['choice'] if isinstance(obj, RegistrationData) else obj['id']
        choice_price = obj.price if isinstance(obj, RegistrationData) else obj['price']
        choice_caption = self._field.data['captions'][choice_id]
        return choice_caption, choice_id, choice_price

    def _build_regitems_data(self, key, regitems):
        name, id, price = key
        choices = lambda r: {choice['id']: choice for choice in r.field_data.versioned_data['choices']}
        data = {'regs': len(regitems),
                'capacity': next((choices(regitem)[regitem.data['choice']]['places_limit'] for regitem in regitems), 0),
                'cancelled': any(not choices(regitem)[regitem.data['choice']]['is_enabled'] for regitem in regitems),
                'billable': bool(price)}
        if data['billable']:
            data['price'] = price
            data['paid'] = sum(1 for regitem in regitems if regitem.registration.is_paid)
            data['paid_amount'] = sum(float(price) for regitem in regitems if regitem.registration.is_paid)
            data['unpaid'] = sum(1 for regitem in regitems if not regitem.registration.is_paid)
            data['unpaid_amount'] = sum(float(price) for regitem in regitems if not regitem.registration.is_paid)
        return DataItem(**data)

    def _build_choice_data(self, choice):
        data = {'capacity': choice['places_limit'],
                'cancelled': not choice['is_enabled'],
                'billable': bool(choice['price'])}
        if choice['price']:
            data['price'] = choice['price']
        return DataItem(**data)

    def _get_table_head(self):
        head = [Cell(type='str', data=_("Accomodation")), Cell(type='str', data=_("Registrants"))]

        if self.has_capacity:
            head.append(Cell(type='str', data=_("Occupancy")))

        if self._show_billing_info:
            head.extend([Cell(type='str', data=_("Price")),
                         Cell(type='str', data=_("Accommodations paid")),
                         Cell(type='str', data=_("Total paid (unpaid)"), colspan=2),
                         Cell(type='str', data=_("Total"))])

        return head

    def _get_main_row_cells(self, data_items, choice_caption, total_regs):
        active_registrations = self._field.registration_form.active_registrations
        cancelled = any(d.cancelled for d in data_items)
        return [
            Cell(type='str', data=' ' + choice_caption, classes=['cancelled-item'] if cancelled else []),
            Cell(type='progress', data=((total_regs / len(active_registrations),
                                         '{} / {}'.format(total_regs, len(active_registrations)))
                                        if active_registrations else None))
        ] + self._get_occupancy(data_items)

    def _get_sub_row_cells(self, data_item, total_regs):
        return [
            Cell(type='str'),
            Cell(type='progress', data=((data_item.regs / total_regs,
                                        '{} / {}'.format(data_item.regs, total_regs))
                                        if total_regs else None)),
        ] + self._get_occupancy_details(data_item)
