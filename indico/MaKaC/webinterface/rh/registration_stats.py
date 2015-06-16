# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from collections import defaultdict, namedtuple
from itertools import groupby
from operator import methodcaller

from indico.util.date_time import now_utc
from indico.util.i18n import _, get_current_locale
from MaKaC.webinterface.pages.registrants import WPRegistrationStats
from MaKaC.webinterface.rh.registrationFormModif import RHRegistrationFormModifBase


class RHRegistrationStats(RHRegistrationFormModifBase):
    def _process(self):
        stats = [
            OverviewStats(self._conf),
            AccommodationStats(self._conf),
            SocialEventsStats(self._conf),
            SessionStats(self._conf),
        ]
        p = WPRegistrationStats(self, self._conf, stats=filter(None, stats))
        return p.display()


class StatsBase(object):
    def __init__(self, conf, title, headline, type, **kwargs):
        """
        Base class for statistics

        Represents a stats "box" with a title, headline and some content derived
        from a conference.

        Each instance also holds the reference to a type which hints at
        how the data should be rendered. Each subclass can define it's
        own type; but a macro to render it must be defined and called in
        `events/registration/stats.html`.

        :param conf: Conference -- the conference object
        :param title: str -- the title for the stats box
        :param headline: str -- the headline for the stats box
        :param type: str -- the type used in Jinja to display the stats
        """
        super(StatsBase, self).__init__(**kwargs)
        self._conf = conf
        self.title = title
        self.headline = headline
        self.type = type

    @property
    def show_currency_info(self):
        """
        Whether to show a small label at the top right corner of the box,
        indicating the currency used in the stats.

        This should be overriden by children accordingly.
        """
        return False

    @property
    def registrants(self):
        return self._conf.getRegistrantsList()

    @property
    def registration_form(self):
        return self._conf.getRegistrationForm()

    @property
    def currency(self):
        """
        The currency used for payments by registrants to the conference.

        Defaults to `CHF` if not set, which happens if e-payment was disabled
        afterwards.

        :returns: str -- the currency abbreviation
        """
        return self._conf.getRegistrationForm().getCurrency() or 'CHF'


class Cell(namedtuple('Cell', ['type', 'colspan', 'classes', 'qtip', 'data'])):
    def __new__(cls, type=None, colspan=1, classes=None, qtip=None, data=None):
        """
        Holds the data and type of for a cell of a stats table.

        Used by the `TableStats` class.

        The format of the data depends on the value (`str`) passed to the type
        argument.
        The table below indicates the valid types and the format of the data
        specific to the type.

        +--------------------+-------------------------------------------------+
        | type               | data                                            |
        +====================+=================================================+
        | `str`              | `str` -- string value                           |
        +--------------------+-------------------------------------------------+
        | `progress`         | `(int, str)` -- a tuple with the progress (a    |
        |                    | value between 0 and 1) and a label              |
        +--------------------+-------------------------------------------------+
        | `progress-stacked` | `([int], str)` -- a tuple with a list of        |
        |                    | progresses (values which must sum up to 1) and  |
        |                    | a label                                         |
        +--------------------+-------------------------------------------------+
        | `currency`         | `float` -- numeric value                        |
        +--------------------+-------------------------------------------------+
        | `icon`             | `str` -- icon name, must be a valid icon from   |
        |                    | `_icons.scss ` (without the `icon-` prefix)     |
        +--------------------+-------------------------------------------------+
        | `default` / `None` | `None` -- renders a default cell with an        |
        |                    | `&mdash;` (use `Cell(type='str')` for an empty  |
        |                    | cell)                                           |
        +--------------------+-------------------------------------------------+

        :param type: str -- The type of data in the cell
        :param colspan: int -- HTML colspan value for the cell
        :param classes: [str] -- HTML classes to apply to the cell
        :param qtip: str -- string to set as value for the HTML `title` attribute,
                            used as content for qtip
        :param data: The data for the cell
        """
        if classes is None:
            classes = []

        # Provide sensible data defaults for specific types
        if data is None:
            if type == 'str':
                data = ''
            elif type == 'progress-stacked':
                data = [[0], '0']
            elif type == 'progress':
                data = (0, '0')
            elif type == 'currency':
                data = 0,
            elif type == 'icon':
                data = 'warning'
        return super(Cell, cls).__new__(cls, type, colspan, classes, qtip, data)

    def render(self, cell_macros):
        """
        Visitor-like function to render the cell content in Jinja.

        The cell_macros is a mapping from the cell type to the macro rendering
        it.
        """
        try:
            macro = cell_macros[self.type]
        except KeyError:
            macro = cell_macros['default']
        return macro(self)


class DataItem(namedtuple('DataItem', ['regs', 'attendance', 'capacity', 'billable', 'cancelled', 'cancel_reason',
                                       'price', 'fixed_price', 'paid', 'paid_amount', 'unpaid', 'unpaid_amount'])):
    def __new__(cls, regs=0, attendance=0, capacity=0, billable=False, cancelled=False, cancel_reason='', price=0,
                fixed_price=False, paid=0, paid_amount=0, unpaid=0, unpaid_amount=0):
        """
        Holds the aggregation of some data, intended for stats tables as a
        aggregation from which to generate cells.

        :param regs: int -- number of registrant
        :param attendance: int -- number of people attending
        :param capacity: int -- maximum number of people allowed to attend (`0`
                         if unlimited)
        :param billable: bool -- whether the item is billable to the or not
        :param cancelled: bool -- whether the item is canceled or not
        :param cancel_reason: str -- reason the item has been canceled `None` if
                              it is not canceled)
        :param price: str -- the price of the item
        :param fixed_price: bool -- `True` if the price is per registrant,
                            `False` if accompanying guests must pay as well.
        :param paid: int -- number of registrants who paid
        :param paid_amount: float -- amount already paid by registrants
        :param unpaid: int -- number of registrants who haven't paid
        :param unpaid_amount: float -- amount not already paid by registrants
        """
        return super(DataItem, cls).__new__(cls, regs, attendance, capacity, billable, cancelled, cancel_reason, price,
                                            fixed_price, paid, paid_amount, unpaid, unpaid_amount)


class TableStats(object):
    def __init__(self, items, reg_items, **kwargs):
        """
        Generates a stats table.

        Takes a list of `items` such as events, sessions, accommodations and so
        on, as well as a list of registration objects (`reg_items`) for said
        `items`.
        """
        kwargs.setdefault('type', 'table')
        super(TableStats, self).__init__(**kwargs)
        self._items = {item.getId(): item for item in items}
        self._reg_items = sorted(reg_items, key=self._key_fn)
        for ritem in self._reg_items:
            item = self._item_from_ritem(ritem)
            self._items.setdefault(item.getId(), item)
        self._data, self._show_billing_info = self._compute_data()

    @property
    def show_currency_info(self):
        return self._show_billing_info

    def _compute_data(self):
        """
        Aggregates and format data from `self._items` and `self._reg_items`
        such that a table can be generated from it.

        :returns: (dict, bool) -- the data and a boolean to indicate whether the
                  data contains billing information or not.
        """
        billed_items = {}
        for k, ritems in groupby((ritem for ritem in self._reg_items if self._is_billable(ritem)), self._key_fn):
            billed_items[k] = self._billed_data_from_ritems(k, list(ritems))
        not_billed_items = {}
        for k, ritems in groupby((ritem for ritem in self._reg_items if not self._is_billable(ritem)),
                                 self._alt_key_fn):
            not_billed_items[k] = self._not_billed_data_from_ritems(k, list(ritems))
        # Add events with no registrants
        for item in self._items.itervalues():
            if self._is_billable(item):
                billed_items.setdefault(self._key_fn(item), self._billed_data_from_item(item))
            else:
                not_billed_items.setdefault(self._alt_key_fn(item), self._not_billed_data_from_item(item))

        data = defaultdict(list)
        for key, item in billed_items.iteritems():
            data[self._get_name_id_from_key(key)].append(item)
        for key, item in not_billed_items.iteritems():
            data[self._get_name_id_from_alt_key(key)].append(item)

        return data, bool(billed_items)

    def get_table(self):
        """
        Returns a table containing the stats for each item.

        If an item has multiple aggregations (determined by the key functions
        `self._key_fn` and `self._alt_key_fn`), this item will have multiple sub
        rows, one for each aggregation of data and a header row which contains
        an aggregation of the sub rows.
        If an item has a single aggregation if will have a single row as a main
        row.

        :return: dict -- A table with a list of head cells (key: `'head'`) and
                  a list of rows (key: `'rows'`) where each row is a list of
                  cells.
        """
        table = defaultdict(list)
        table['head'] = self._get_table_head()

        for (name, id), item_details in sorted(self._data.iteritems()):
            num_regs = sum(detail.regs for detail in item_details)
            cancel_reason = self._cancel_reason_from_item(item_details)

            # Header/Single row
            table['rows'].append(('single-row' if len(item_details) == 1 else 'header-row',
                                 self._get_main_row(item_details, name, num_regs, cancel_reason) +
                                 self._get_billing(item_details)))

            if len(item_details) == 1:
                continue

            # Optional sub-rows
            table['rows'].extend(('sub-row', self._get_sub_row(detail, num_regs) + self._get_billing_details(detail))
                                 for detail in item_details)
        return table

    def __nonzero__(self):
        """
        Used to indicate whether the stats should be displayed or not depending
        if there is data or not.
        """
        return bool(self._data)

    def _is_billable(self, item):
        """
        Convenience method to indicate if an item is billable.

        This can be overridden by children.

        :returns: bool -- `True` if the item is billable, false otherwise
        """
        return item.isBillable() and float(item.getPrice()) > 0

    def _get_billing(self, item_details):
        """
        Returns the cells with billing information, in order, for a main row
        (header or single row).

        :params item_details: [DataItem] -- list of aggregation for which to
                              generate the cells.
        :returns: [Cell] -- a list of cells with billing information in order.
        """
        # hide billing details if no session require payments
        if not self._show_billing_info:
            return []

        # Only paid or unpaid accommodation so we move the sub row up as the
        # header row.
        if len(item_details) == 1:
            return self._get_billing_details(item_details[0])

        paid = sum(detail.paid for detail in item_details if detail.billable)
        paid_amount = sum(detail.paid_amount for detail in item_details if detail.billable)

        unpaid = sum(detail.unpaid for detail in item_details if detail.billable)
        unpaid_amount = sum(detail.unpaid_amount for detail in item_details if detail.billable)

        total = paid + unpaid
        total_amount = paid_amount + unpaid_amount

        progress = [[float(paid) / total, float(unpaid) / total], '{} / {}'.format(paid, total)] if total else None

        return [Cell(),  # no price for aggregation of details
                Cell(type='progress-stacked', data=progress, classes=['paid-unpaid-progress']),
                Cell(type='currency', data=paid_amount, classes=['paid-amount', 'stick-left']),
                Cell(type='currency', data=unpaid_amount, classes=['unpaid-amount', 'stick-right']),
                Cell(type='currency', data=total_amount)]

    def _get_billing_details(self, detail):
        """
        Returns the cells with billing information, in order, for a sub row.

        :params item_details: DataItem -- aggregation for which to generate the
                              cells.
        :returns: [Cell] -- a list of cells with billing information in order.
        """
        if not self._show_billing_info:  # hide billing details if no events require payments
            return []

        if not detail.billable:
            return [Cell(type='currency', data=0),
                    Cell(),  # mdash (default content) instead of a paid progress bar
                    Cell(type='currency', data=0, classes=['paid-amount', 'stick-left']),
                    Cell(type='currency', data=0, classes=['unpaid-amount', 'stick-right']),
                    Cell(type='currency', data=0)]

        progress = [[float(detail.paid) / detail.regs, float(detail.unpaid) / detail.regs],
                    '{0.paid} / {0.regs}'.format(detail)] if detail.regs else None

        return [
            Cell(type='currency', data=float(detail.price)),
            Cell(type='progress-stacked', data=progress, classes=['paid-unpaid-progress']),
            Cell(type='currency', data=detail.paid_amount, classes=['paid-amount', 'stick-left']),
            Cell(type='currency', data=detail.unpaid_amount, classes=['unpaid-amount', 'stick-right']),
            Cell(type='currency', data=detail.paid_amount + detail.unpaid_amount)
        ]

    def _item_from_ritem(self, ritem):
        """
        Returns an "item: of similar type as the items in `self._items` given an
        "ritem" from `self._reg_items`.

        Must be overridden by children accordingly based on items and reg items.
        """
        raise NotImplementedError

    def _key_fn(self, item):
        """
        The key function used to sort and group by reg items.

        It must include the name (title or caption) and the id of the item.
        This should also include the price or other billing information by which
        to aggregate.

        :param item: the item from which to derive a key.
        :returns: tuple -- tuple to be used as a key to sort and group items by.
        """
        raise NotImplementedError

    def _alt_key_fn(self, item):
        """
        The alternate key function used to sort and group by reg items.

        It must include the name (title or caption) and the id of the item.
        This should explicitly not include the price or other billing
        information in order to identify free reg items.

        :param item: the item from which to derive a key.
        :returns: tuple -- tuple to be used as a key to sort and group items by.
        """
        raise NotImplementedError

    def _billed_data_from_ritems(self, key, ritems):
        """
        Returns a `DataItem` containing the aggregation of reg items (`ritems`)
        which are billed to the registrants.

        :param ritems: list -- list of reg items to be aggregated
        :returns: DataItem -- the aggregation of the `ritems`
        """
        raise NotImplementedError

    def _not_billed_data_from_ritems(self, key, ritems):
        """
        Returns a `DataItem` containing the aggregation of reg items (`ritems`)
        which are not billed to the registrants.

        :param ritems: list -- list of reg items to be aggregated
        :returns: DataItem -- the aggregation of the `ritems`
        """
        raise NotImplementedError

    def _billed_data_from_item(self, item):
        """
        Returns a `DataItem` containing the aggregation of an item which is
        billed to the registrants.

        :param item: list -- item to be aggregated
        :returns: DataItem -- the aggregation of the `item`
        """
        raise NotImplementedError

    def _not_billed_data_from_item(self, item):
        """
        Returns a `DataItem` containing the aggregation of an item which is not
        billed to the registrants.

        :param item: list -- item to be aggregated
        :returns: DataItem -- the aggregation of the `item`
        """
        raise NotImplementedError

    def _get_name_id_from_key(self, key):
        """
        Returns the name and id of an item from its key.

        The key corresponds to output of `self._key_fn` for a given item.

        :returns: (name, id) -- a tuple containing the name and id of item
        """
        raise NotImplementedError

    def _get_name_id_from_alt_key(self, key):
        """
        Returns the name and id of an item from its key.

        The key corresponds to output of `self._alt_key_fn` for a given item.

        :returns: (name, id) -- a tuple containing the name and id of item
        """
        raise NotImplementedError

    def _get_table_head(self):
        """
        Returns a list of `Cell` corresponding to the headers of a the table.

        :returns: [Cell] -- the headers of the table.
        """
        raise NotImplementedError

    def _cancel_reason_from_item(self, details):
        """
        Returns a cancel reason from a list of `DataItem`.

        If any item in the list of `DataItem` has the cancelled flag set,
        returns a first cancel_reason from the list of `DataItem`.

        If no cancel reason is found, a default reason should be returned.

        Returns `None` if nono of the `cancelled` flag are set.

        :param details: [DataItem] -- a list of items w
        :returns: str -- a cancel reason if an item has the `cancelled` flag
                         set, `None` otherwise.
        """
        raise NotImplementedError

    def _get_main_row(self, item_details, item_name, num_regs, cancel_reason):
        """
        Returns the cells of the main (header or single) row of the table.

        Each `item` has a main row. The row is a list of `Cell` which matches
        the table head.

        :param item_details: [DataItem] -- list of aggregations for the item
        :param item_name: str -- the item's name
        :param num_regs: int -- the number of registrants for the item
        :param cancel_reason: str -- the cancel reason for this item if it is
                              canceled, `None` otherwise

        :returns: [Cell] -- the list of cells constituting the row.
        """
        raise NotImplementedError

    def _get_sub_row(self, details, num_regs):
        """
        Returns the cells of the sub row of the table.

        An `item` cna have a sub row. The row is a list of `Cell` which matches
        the table head.

        :param details: DataItem -- aggregation for the item
        :param num_regs: int -- the number of registrants for the item

        :returns: [Cell] -- the list of cells constituting the row.
        """
        raise NotImplementedError


class OverviewStats(StatsBase):
    def __init__(self, conf):
        """
        Generic stats showing an overview for the conference.

        Shows the following:
            - number of registrants
            - days left to register
            - number of countries of origins from registrants
            - availability of the conference
            - repartition of registrants per country of origin (for top 15
              countries)
        """
        super(OverviewStats, self).__init__(conf=conf, title=_("Overview"), headline="", template='stats_overview.html')
        self.registrants_sorted = sorted(self.registrants, key=methodcaller('getCountry'))  # sort for groupby
        self.countries, self.num_countries = self._compute_countries()
        self.availability = self._compute_availibility()
        self.days_left = max(0, (self.registration_form.getAllowedEndRegistrationDate() - now_utc()).days)

    def _compute_countries(self):
        locale = get_current_locale()
        countries = defaultdict(int)
        for country_code, regs in groupby(self.registrants_sorted, methodcaller('getCountry')):
            country = locale.territories.get(country_code)
            countries[country] += sum(1 for x in regs)
        others = [countries.pop(None, 0), _("Others")]
        if not countries:  # no country data for any registrants
            return [], 0
        num_countries = len(countries)
        # Sort by highest number of people per country then alphabetically per countries' name
        countries = sorted(((val, name) for name, val in countries.iteritems()), key=lambda x: (-x[0], x[1]),
                           reverse=True)
        others[0] += sum(val for val, name in countries[:-15])
        return ([others] if others[0] else []) + countries[-15:], num_countries

    def _compute_availibility(self):
        users_limit = self.registration_form.getUsersLimit()
        if not users_limit or self.registration_form.isFull():
            return (0, 0, 0)
        return (len(self.registrants), users_limit, float(len(self.registrants)) / users_limit)

    def __nonzero__(self):
        return True


class AccommodationStats(TableStats, StatsBase):
    def __init__(self, conf):
        super(AccommodationStats, self).__init__(
            conf=conf, title=_("Accommodation"), headline="", template='stats_accomodation.html',
            items=conf.getRegistrationForm().getAccommodationForm().getAccommodationTypesList(),
            reg_items=(r.getAccommodation() for r in conf.getRegistrantsList()
                       if r.getAccommodation() is not None and r.getAccommodation().getAccommodationType() is not None)
        )
        self.has_capacity = any(detail.capacity for acco_details in self._data.itervalues()
                                for detail in acco_details if detail.capacity)

    def _get_occupancy(self, acco_details):
        if not self.has_capacity:
            return []
        capacity = max(d.capacity for d in acco_details)
        if not capacity:
            return [Cell()]
        regs = sum(d.regs for d in acco_details)
        return [Cell(type='progress', data=(float(regs) / capacity, '{} / {}'.format(regs, capacity)))]

    def _get_occupancy_details(self, details):
        if not self.has_capacity:
            return []
        if not details.capacity:
            return [Cell()]
        return [Cell(type='progress',
                     data=(float(details.regs) / details.capacity, '{0.regs} / {0.capacity}'.format(details)))]

    def _item_from_ritem(self, reg_acco):
        return reg_acco.getAccommodationType()

    def _key_fn(self, acco):
        return (acco.getCaption(), acco.getId(), acco.getPrice())

    def _alt_key_fn(self, acco):
        return (acco.getCaption(), acco.getId())

    def _billed_data_from_ritems(self, key, acco_details):
        name, id, price = key
        return DataItem(
            regs=len(acco_details),
            capacity=next((detail.getAccommodationType().getPlacesLimit() for detail in acco_details), 0),
            billable=True,
            cancelled=any(detail.isCancelled() for detail in acco_details),
            price=price,
            paid=len([detail for detail in acco_details if detail.getRegistrant().getPayed()]),
            paid_amount=sum(float(price) for detail in acco_details if detail.getRegistrant().getPayed()),
            unpaid=len([detail for detail in acco_details if not detail.getRegistrant().getPayed()]),
            unpaid_amount=sum(float(price) for detail in acco_details if not detail.getRegistrant().getPayed())
        )

    def _not_billed_data_from_ritems(self, key, acco_details):
        name, id = key
        return DataItem(
            regs=len(acco_details),
            capacity=next((a.getAccommodationType().getPlacesLimit() for a in acco_details), 0),
            billable=False,
            cancelled=any(a.isCancelled() for a in acco_details)
        )

    def _billed_data_from_item(self, acco):
        return DataItem(
            capacity=acco.getPlacesLimit(),
            billable=True,
            cancelled=acco.isCancelled(),
            price=acco.getPrice()
        )

    def _not_billed_data_from_item(self, acco):
        return DataItem(
            capacity=acco.getPlacesLimit(),
            billable=False,
            cancelled=acco.isCancelled()
        )

    def _get_name_id_from_key(self, key):
        return key[:2]  # key = name, id, price, price_per_place

    def _get_name_id_from_alt_key(self, key):
        return key  # key = name, id

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

    def _cancel_reason_from_item(self, acco_details):
        return _("Accommodation unavailable") if any(detail.cancelled for detail in acco_details) else None

    def _get_main_row(self, acco_details, acco_name, num_regs, cancel_reason):
        return [
            Cell(type='str', data=' ' + acco_name, classes=['cancelled-item'] if cancel_reason else [],
                 qtip=cancel_reason),
            Cell(type='progress', data=((float(num_regs) / len(self.registrants),
                                         '{} / {}'.format(num_regs, len(self.registrants)))
                                        if self.registrants else None))
        ] + self._get_occupancy(acco_details)

    def _get_sub_row(self, details, num_regs):
        return [
            Cell(type='str'),
            Cell(type='progress', data=((float(details.regs) / num_regs, '{} / {}'.format(details.regs, num_regs))
                                        if num_regs else None)),
        ] + self._get_occupancy_details(details)

    def __nonzero__(self):
        return (self.registration_form.getAccommodationForm().isEnabled() and
                super(AccommodationStats, self).__nonzero__())


class SessionStats(TableStats, StatsBase):
    def __init__(self, conf):
        super(SessionStats, self).__init__(
            conf=conf, title=_("Sessions"), headline="", template='stats_sessions.html',
            items=(reg_ses for reg_ses in conf.getRegistrationForm().getSessionsForm().getSessionList()
                   if reg_ses.getSession() is not None),
            reg_items=(reg_ses for r in conf.getRegistrantsList() for reg_ses in r.getSessionList()
                       if reg_ses.getSession() is not None)
        )

    def _item_from_ritem(self, rses):
        return rses

    def _key_fn(self, rses):
        return (rses.getTitle(), rses.getId(), rses.getPrice())

    def _alt_key_fn(self, rses):
        return (rses.getTitle(), rses.getId())

    def _billed_data_from_ritems(self, key, ses_details):
        name, id, price = key
        return DataItem(
            regs=len(ses_details),
            billable=True,
            cancelled=any(detail.isCancelled() for detail in ses_details),
            price=price,
            paid=len([detail for detail in ses_details if detail.getRegistrant().getPayed()]),
            paid_amount=sum(float(detail.getPrice()) for detail in ses_details if detail.getRegistrant().getPayed()),
            unpaid=len([detail for detail in ses_details if not detail.getRegistrant().getPayed()]),
            unpaid_amount=sum(float(price) for detail in ses_details if not detail.getRegistrant().getPayed())
        )

    def _not_billed_data_from_ritems(self, key, ses_details):
        return DataItem(regs=len(ses_details), billable=False,
                        cancelled=any(detail.isCancelled() for detail in ses_details))

    def _billed_data_from_item(self, ses_detail):
        return DataItem(billable=True, cancelled=ses_detail.isCancelled(), price=ses_detail.getPrice())

    def _not_billed_data_from_item(self, ses_detail):
        return DataItem(billable=False, cancelled=ses_detail.isCancelled())

    def _get_name_id_from_key(self, key):
        return key[:2]  # key = name, id, price

    def _get_name_id_from_alt_key(self, key):
        return key  # key = name, id

    def _get_table_head(self):
        head = [Cell(type='str', data=_("Sessions")), Cell(type='str', data=_("Registrants"))]

        if self._show_billing_info:
            head.extend([Cell(type='str', data=_("Price")),
                         Cell(type='str', data=_("Sessions paid")),
                         Cell(type='str', data=_("Total paid (unpaid)"), colspan=2),
                         Cell(type='str', data=_("Total"))])

        return head

    def _cancel_reason_from_item(self, ses_details):
        return _("Session cancelled") if any(detail.cancelled for detail in ses_details) else None

    def _get_main_row(self, ses_details, ses_name, num_regs, cancel_reason):
        return [Cell(type='str', data=' ' + ses_name, classes=['cancelled-item'] if cancel_reason else [],
                     qtip=cancel_reason),
                Cell(type='progress', data=((float(num_regs) / len(self.registrants),
                                             '{} / {}'.format(num_regs, len(self.registrants)))
                                            if self.registrants else None))]

    def _get_sub_row(self, details, num_regs):
        return [Cell(type='str'),
                Cell(type='progress', data=((float(details.regs) / num_regs, '{} / {}'.format(details.regs, num_regs))
                                            if num_regs else None))]

    def __nonzero__(self):
        return (self.registration_form.getSessionsForm().isEnabled() and
                super(SessionStats, self).__nonzero__())


class SocialEventsStats(TableStats, StatsBase):
    def __init__(self, conf):
        super(SocialEventsStats, self).__init__(
            conf=conf, title=None, headline=None, template='stats_social_events.html',
            items=(e for e in conf.getRegistrationForm().getSocialEventForm().getSocialEventList() if e is not None),
            reg_items=(re for r in conf.getRegistrantsList() for re in r.getSocialEvents() if re is not None))
        self._form = self._conf.getRegistrationForm().getSocialEventForm()
        # Override title and headline
        self.title = self._form.getTitle()
        self.headline = _("Registrants {} select {}.").format(
            '<b>{}</b>'.format(_("must")) if self.mandatory else _("can"),
            _("multiple events") if self.selection_type == "multiple" else _("a unique event")
        )

    @property
    def selection_type(self):
        return self._form.getSelectionTypeId()

    @property
    def mandatory(self):
        return self._form.getMandatory()

    def _compute_amount(self, event):
        return (float(event.getPrice()) * event.getNoPlaces()) if event.isPricePerPlace() else float(event.getPrice())

    def _get_attendance(self, evt_details):
        capacity = next((detail.capacity for detail in evt_details if detail.capacity), 0)
        if not capacity:
            return Cell(type='str', data=sum(detail.attendance for detail in evt_details))

        attendance = next((detail.attendance for detail in evt_details if detail.attendance), 0)
        label = '{} / {}'.format(attendance, capacity)
        qtip = '{} attendees, {} place(s) available'.format(attendance, capacity - attendance)
        return Cell(type='progress', qtip=qtip, data=(float(attendance) / capacity, label))

    def _item_from_ritem(self, reg_event):
        return reg_event.getSocialEventItem()

    def _key_fn(self, event):
        return (event.getCaption(), event.getId(), event.getPrice(), event.isPricePerPlace())

    def _alt_key_fn(self, event):
        return (event.getCaption(), event.getId())

    def _billed_data_from_ritems(self, key, evt_details):
        name, id, price, price_per_place = key
        return DataItem(
            regs=len(evt_details),
            attendance=next((detail.getSocialEventItem().getCurrentNoPlaces()
                            for detail in evt_details if detail.getSocialEventItem().getCurrentNoPlaces()), 0),
            capacity=next((detail.getSocialEventItem().getPlacesLimit()
                          for detail in evt_details if detail.getSocialEventItem().getPlacesLimit()), 0),
            billable=True,
            cancelled=any(detail.isCancelled() for detail in evt_details),
            cancel_reason=next((detail.getCancelledReason() for detail in evt_details if detail.getCancelledReason()),
                               None),
            price=price,
            fixed_price=not price_per_place,
            paid=len([detail for detail in evt_details if detail.getRegistrant().getPayed()]),
            paid_amount=sum(self._compute_amount(detail) for detail in evt_details
                            if detail.getRegistrant().getPayed()),
            unpaid=len([detail for detail in evt_details if not detail.getRegistrant().getPayed()]),
            unpaid_amount=sum(self._compute_amount(detail) for detail in evt_details
                              if not detail.getRegistrant().getPayed())
        )

    def _not_billed_data_from_ritems(self, key, evt_details):
        return DataItem(
            regs=len(evt_details),
            attendance=next((detail.getSocialEventItem().getCurrentNoPlaces()
                             for detail in evt_details if detail.getSocialEventItem().getCurrentNoPlaces()), 0),
            capacity=next((detail.getSocialEventItem().getPlacesLimit()
                           for detail in evt_details if detail.getSocialEventItem().getPlacesLimit()), 0),
            billable=False,
            cancelled=any(detail.isCancelled() for detail in evt_details),
            cancel_reason=next((detail.getCancelledReason() for detail in evt_details
                               if detail.getCancelledReason()), None),
            price=next((detail.getPrice() for detail in evt_details), 0)
        )

    def _billed_data_from_item(self, event):
        return DataItem(
            capacity=event.getPlacesLimit(),
            billable=True,
            cancelled=event.isCancelled(),
            cancel_reason=event.getCancelledReason() if event.getCancelledReason() else '',
            price=event.getPrice(),
            fixed_price=not event.isPricePerPlace()
        )

    def _not_billed_data_from_item(self, event):
        return DataItem(
            capacity=event.getPlacesLimit(),
            billable=False,
            price=event.getPrice(),
            fixed_price=not event.isPricePerPlace()
        )

    def _get_name_id_from_key(self, key):
        return key[:2]  # key = name, id, price, price_per_place

    def _get_name_id_from_alt_key(self, key):
        return key  # key = name, id

    def _get_table_head(self):
        head = [Cell(type='str', data=_("Event")),
                Cell(type='str', data=_("Registrants")),
                Cell(type='str', data=_("Attendees"))]

        if self._show_billing_info:
            head.extend([
                Cell(type='str', data=_("Price"), colspan=2),
                Cell(type='str', data=_("Registrations paid")),
                Cell(type='str', data=_("Total paid (unpaid)"), colspan=2),
                Cell(type='str', data=_("Total"))
            ])

        return head

    def _cancel_reason_from_item(self, evt_details):
        return (_("Cancelled: {}").format(next((detail.cancel_reason for detail in evt_details if detail.cancel_reason),
                                               _("No reason given")))
                if any(detail.cancelled for detail in evt_details) else None)

    def _get_main_row(self, event_details, event_name, num_regs, cancel_reason):
        return [Cell(type='str', data=' ' + event_name, classes=['cancelled-item'] if cancel_reason else [],
                     qtip=cancel_reason),
                Cell(type='progress', data=(float(num_regs) / len(self.registrants), '{} / {}'.format(num_regs,
                     len(self.registrants))) if self.registrants else None),
                self._get_attendance(event_details)]

    def _get_sub_row(self, details, num_regs):
        return [Cell(type='str'),
                Cell(type='progress', data=((float(details.regs) / num_regs, '{} / {}'.format(details.regs, num_regs))
                                            if num_regs else None)),
                self._get_attendance([details])]

    def _get_billing(self, evt_details):
        # Only one kind of payment (currency, price and fixed price or not)
        # or only no payment so we move the sub row up as the header row.
        if len(evt_details) == 1:
            return self._get_billing_details(evt_details[0])

        billing_cells = super(SocialEventsStats, self)._get_billing(evt_details)
        # the icon next to the price for social events takes an extra cell
        if billing_cells:
            billing_cells[0] = Cell(colspan=2)

        return billing_cells

    def _get_billing_details(self, details):
        billing_cells = super(SocialEventsStats, self)._get_billing_details(details)
        if not billing_cells:  # no billing details
            return billing_cells

        # The users icon is displayed when accompanying guests must pay as well.
        price_details = (Cell(type='str', classes=['stick-left']) if details.fixed_price else
                         Cell(type='icon', data='users', qtip='accompanying guests must pay', classes=['stick-left']))

        return [price_details] + billing_cells

    def __nonzero__(self):
        return (self.registration_form.getSocialEventForm().isEnabled() and
                super(SocialEventsStats, self).__nonzero__())
