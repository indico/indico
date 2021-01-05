# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

import json
from collections import OrderedDict
from datetime import time, timedelta

import dateutil.parser
import pytz
from flask import session
from markupsafe import escape
from wtforms import Field, SelectField
from wtforms.ext.dateutil.fields import DateField, DateTimeField
from wtforms.fields import TimeField
from wtforms.validators import StopValidation

from indico.core.config import config
from indico.util.date_time import localize_as_utc, relativedelta
from indico.util.i18n import _, get_current_locale
from indico.web.forms.fields import JSONField
from indico.web.forms.validators import DateRange, DateTimeRange, LinkedDate, LinkedDateTime
from indico.web.forms.widgets import JinjaWidget


class TimeDeltaField(Field):
    """A field that lets the user select a simple timedelta.

    It does not support mixing multiple units, but it is smart enough
    to switch to a different unit to represent a timedelta that could
    not be represented otherwise.

    :param units: The available units. Must be a tuple containing any
                  any of 'seconds', 'minutes', 'hours' and 'days'.
                  If not specified, ``('hours', 'days')`` is assumed.
    """

    widget = JinjaWidget('forms/timedelta_widget.html', single_line=True, single_kwargs=True)
    # XXX: do not translate, "Minutes" is ambiguous without context
    unit_names = {
        'seconds': 'Seconds',
        'minutes': 'Minutes',
        'hours': 'Hours',
        'days': 'Days'
    }
    magnitudes = OrderedDict([
        ('days', 86400),
        ('hours', 3600),
        ('minutes', 60),
        ('seconds', 1)
    ])

    def __init__(self, *args, **kwargs):
        self.units = kwargs.pop('units', ('hours', 'days'))
        super(TimeDeltaField, self).__init__(*args, **kwargs)

    @property
    def best_unit(self):
        """Return the largest unit that covers the current timedelta."""
        if self.data is None:
            return None
        seconds = int(self.data.total_seconds())
        for unit, magnitude in self.magnitudes.iteritems():
            if not seconds % magnitude:
                return unit
        return 'seconds'

    @property
    def choices(self):
        best_unit = self.best_unit
        choices = [(unit, self.unit_names[unit]) for unit in self.units]
        # Add whatever unit is necessary to represent the currenet value if we have one
        if best_unit and best_unit not in self.units:
            choices.append((best_unit, '({})'.format(self.unit_names[best_unit])))
        return choices

    def process_formdata(self, valuelist):
        if valuelist and len(valuelist) == 2:
            value = int(valuelist[0])
            unit = valuelist[1]
            if unit not in self.magnitudes:
                raise ValueError('Invalid unit')
            self.data = timedelta(seconds=self.magnitudes[unit] * value)

    def pre_validate(self, form):
        if self.best_unit in self.units:
            return
        if self.object_data is None:
            raise ValueError(_('Please choose a valid unit.'))
        if self.object_data != self.data:
            raise ValueError(_('Please choose a different unit or keep the previous value.'))

    def _value(self):
        if self.data is None:
            return '', ''
        else:
            return int(self.data.total_seconds()) // self.magnitudes[self.best_unit], self.best_unit


class RelativeDeltaField(Field):
    """A field that lets the user select a simple timedelta.

    It does not support mixing multiple units, but it is smart enough
    to switch to a different unit to represent a timedelta that could
    not be represented otherwise.

    :param units: The available units. Must be a tuple containing any
                  any of 'seconds', 'minutes', 'hours' and 'days'.
                  If not specified, ``('hours', 'days')`` is assumed.
    """

    widget = JinjaWidget('forms/timedelta_widget.html', single_line=True, single_kwargs=True)
    # XXX: do not translate, "Minutes" is ambiguous without context
    unit_names = {
        'seconds': 'Seconds',
        'minutes': 'Minutes',
        'hours': 'Hours',
        'days': 'Days',
        'weeks': 'Weeks',
        'months': 'Months',
        'years': 'Years'
    }
    magnitudes = OrderedDict([
        ('years', relativedelta(years=1)),
        ('months', relativedelta(months=1)),
        ('weeks', relativedelta(weeks=1)),
        ('days', relativedelta(days=1)),
        ('hours', relativedelta(hours=1)),
        ('minutes', relativedelta(minutes=1)),
        ('seconds', relativedelta(seconds=1))
    ])

    def __init__(self, *args, **kwargs):
        self.units = kwargs.pop('units', ('hours', 'days'))
        super(RelativeDeltaField, self).__init__(*args, **kwargs)

    @property
    def split_data(self):
        if self.data is None:
            return None, None
        for unit in self.magnitudes:
            number = getattr(self.data, unit)
            if number:
                return number, unit
        raise ValueError('Unsupported relativedelta() unit')

    @property
    def choices(self):
        choices = [(unit, self.unit_names[unit]) for unit in self.units]
        number, unit = self.split_data
        if number is not None and unit not in self.units:
            # Add whatever unit is necessary to represent the currenet value if we have one
            choices.append((unit, '({})'.format(self.unit_names[unit])))
        return choices

    def process_formdata(self, valuelist):
        if valuelist and len(valuelist) == 2:
            value = int(valuelist[0])
            unit = valuelist[1]
            if unit not in self.magnitudes:
                raise ValueError('Invalid unit')
            self.data = (self.magnitudes[unit] * value).normalized()

    def pre_validate(self, form):
        if self.object_data is None:
            raise ValueError(_('Please choose a valid unit.'))

    def _value(self):
        if self.data is None:
            return '', ''
        return self.split_data


class IndicoTimeField(TimeField):
    widget = JinjaWidget('forms/time_widget.html', single_line=True, single_kwargs=True)


class IndicoDateField(DateField):
    widget = JinjaWidget('forms/date_widget.html', single_line=True, single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.allow_clear = kwargs.pop('allow_clear', None)
        super(IndicoDateField, self).__init__(*args, parse_kwargs={'dayfirst': True},
                                              display_format='%d/%m/%Y', **kwargs)
        if self.allow_clear is None:
            self.allow_clear = not self.flags.required

    @property
    def earliest_date(self):
        if self.flags.date_range:
            for validator in self.validators:
                if isinstance(validator, DateRange):
                    return validator.get_earliest(self.get_form(), self)

    @property
    def latest_date(self):
        if self.flags.date_range:
            for validator in self.validators:
                if isinstance(validator, DateRange):
                    return validator.get_latest(self.get_form(), self)

    @property
    def linked_field(self):
        validator = self.linked_date_validator
        return validator.linked_field if validator else None

    @property
    def linked_date_validator(self):
        if self.flags.linked_date:
            for validator in self.validators:
                if isinstance(validator, LinkedDate):
                    return validator


class IndicoDateTimeField(DateTimeField):
    """Friendly datetime field that handles timezones and validations.

    Important: When the form has a `timezone` field it must be
    declared before any `IndicoDateTimeField`.  Otherwise its
    value is not available in this field resulting in an error
    during form submission.
    """

    widget = JinjaWidget('forms/datetime_widget.html', single_line=True, single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self._timezone = kwargs.pop('timezone', None)
        self.default_time = kwargs.pop('default_time', time(0, 0))
        self.date_missing = False
        self.time_missing = False
        self.allow_clear = kwargs.pop('allow_clear', None)
        super(IndicoDateTimeField, self).__init__(*args, parse_kwargs={'dayfirst': True}, **kwargs)
        if self.allow_clear is None:
            self.allow_clear = not self.flags.required

    def pre_validate(self, form):
        if self.date_missing:
            raise StopValidation(_("Date must be specified"))
        if self.time_missing:
            raise StopValidation(_("Time must be specified"))
        if self.object_data:
            # Normalize datetime resolution of passed data
            self.object_data = self.object_data.replace(second=0, microsecond=0)

    def process_formdata(self, valuelist):
        if any(valuelist):
            if not valuelist[0]:
                self.date_missing = True
            if len(valuelist) < 2 or not valuelist[1]:
                self.time_missing = True
        if valuelist:
            valuelist = [' '.join(valuelist).strip()]
        super(IndicoDateTimeField, self).process_formdata(valuelist)
        if self.data and not self.data.tzinfo:
            self.data = localize_as_utc(self.data, self.timezone)

    @property
    def earliest_dt(self):
        if self.flags.datetime_range:
            for validator in self.validators:
                if isinstance(validator, DateTimeRange):
                    return validator.get_earliest(self.get_form(), self)

    @property
    def latest_dt(self):
        if self.flags.datetime_range:
            for validator in self.validators:
                if isinstance(validator, DateTimeRange):
                    return validator.get_latest(self.get_form(), self)

    @property
    def linked_datetime_validator(self):
        if self.flags.linked_datetime:
            for validator in self.validators:
                if isinstance(validator, LinkedDateTime):
                    return validator

    @property
    def linked_field(self):
        validator = self.linked_datetime_validator
        return validator.linked_field if validator else None

    @property
    def timezone_field(self):
        field = getattr(self.get_form(), 'timezone', None)
        return field if isinstance(field, SelectField) else None

    @property
    def timezone(self):
        if self._timezone:
            return self._timezone
        elif self.timezone_field:
            return self.timezone_field.data
        else:
            form = self.get_form()
            if form and hasattr(form, 'timezone'):
                return form.timezone
            return session.tzinfo.zone

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)


class OccurrencesField(JSONField):
    """
    A field that lets you select multiple occurrences consisting of a
    start date/time and a duration.
    """

    widget = JinjaWidget('forms/occurrences_widget.html', single_line=True)
    CAN_POPULATE = True

    def __init__(self, *args, **kwargs):
        self._timezone = kwargs.pop('timezone', None)
        kwargs.setdefault('default', [])
        super(OccurrencesField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        def _deserialize(occ):
            try:
                dt = dateutil.parser.parse('{} {}'.format(occ['date'], occ['time']))
            except ValueError:
                raise ValueError('Invalid date/time: {} {}'.format(escape(occ['date']), escape(occ['time'])))
            if occ['duration'] < 1:
                raise ValueError('Invalid duration')
            return localize_as_utc(dt, self.timezone), timedelta(minutes=occ['duration'])

        self.data = []
        super(OccurrencesField, self).process_formdata(valuelist)
        self.data = map(_deserialize, self.data)

    def _value(self):
        def _serialize(occ):
            if isinstance(occ, dict):
                # raw data from the client
                return occ
            dt = occ[0].astimezone(pytz.timezone(self.timezone))
            return {'date': dt.date().isoformat(),
                    'time': dt.time().isoformat()[:-3],  # hh:mm only
                    'duration': int(occ[1].total_seconds() // 60)}

        return json.dumps(map(_serialize, self.data))

    @property
    def timezone_field(self):
        field = getattr(self.get_form(), 'timezone', None)
        return field if isinstance(field, SelectField) else None

    @property
    def timezone(self):
        if self.timezone_field:
            return self.timezone_field.data
        else:
            return getattr(self.get_form(), 'timezone', session.tzinfo.zone)


class IndicoTimezoneSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        super(IndicoTimezoneSelectField, self).__init__(*args, **kwargs)
        self.choices = [(v, v) for v in pytz.common_timezones]
        self.default = config.DEFAULT_TIMEZONE

    def process_data(self, value):
        super(IndicoTimezoneSelectField, self).process_data(value)
        if self.data is not None and self.data not in pytz.common_timezones_set:
            self.choices.append((self.data, self.data))


class IndicoWeekDayRepetitionField(Field):
    """Field that lets you select an ordinal day of the week."""

    widget = JinjaWidget('forms/week_day_repetition_widget.html', single_line=True)

    WEEK_DAY_NUMBER_CHOICES = (
        (1, _('first')),
        (2, _('second')),
        (3, _('third')),
        (4, _('fourth')),
        (-1, _('last'))
    )

    def __init__(self, *args, **kwargs):
        locale = get_current_locale()
        self.day_number_options = self.WEEK_DAY_NUMBER_CHOICES
        self.week_day_options = [(n, locale.weekday(n, short=False)) for n in xrange(7)]
        self.day_number_missing = False
        self.week_day_missing = False
        super(IndicoWeekDayRepetitionField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        self.data = ()
        if any(valuelist):
            if not valuelist[0]:
                self.day_number_missing = True
            if not valuelist[1]:
                self.week_day_missing = True
        if valuelist:
            self.data = tuple(map(int, valuelist))

    @property
    def day_number_data(self):
        return self.data[0] if len(self.data) > 0 else None

    @property
    def week_day_data(self):
        return self.data[1] if len(self.data) > 1 else None
