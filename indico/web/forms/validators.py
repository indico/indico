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

from __future__ import unicode_literals

from wtforms.validators import StopValidation, ValidationError, EqualTo

from indico.util.date_time import as_utc, format_datetime, now_utc
from indico.util.i18n import _, ngettext
from indico.util.string import is_valid_mail


class UsedIf(object):
    """Makes a WTF field "used" if a given condition evaluates to True.

    If the field is not used, validation stops.
    """
    field_flags = ('conditional',)

    def __init__(self, condition):
        self.condition = condition

    def __call__(self, form, field):
        if self.condition in (True, False):
            if not self.condition:
                field.errors[:] = []
                raise StopValidation()
        elif not self.condition(form, field):
            field.errors[:] = []
            raise StopValidation()


class HiddenUnless(object):
    """Hides and disables a field unless another field has a certain value.

    :param field: The name of the other field to check
    :param value: The value to check for.  If unspecified, any truthy
                  value is accepted.
    """
    field_flags = ('initially_hidden',)

    def __init__(self, field, value=None):
        self.field = field
        self.value = value

    def __call__(self, form, field):
        value = form[self.field].data
        active = (value and self.value is None) or (value == self.value and self.value is not None)
        if not active:
            field.errors[:] = []
            if field.raw_data:
                raise ValidationError("Received data for disabled field")
            # Clear existing data and use field default empty value
            field.data = None
            field.process_formdata([])
            raise StopValidation()


class Exclusive(object):
    """Makes a WTF field mutually exclusive with other fields.

    If any of the given fields have a value, the validated field may not have one.
    """
    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, form, field):
        if field.data is None:
            return
        if any(form[f].data is not None for f in self.fields):
            field_names = sorted(unicode(form[f].label.text) for f in self.fields)
            msg = ngettext(u'This field is mutually exclusive with another field: {}',
                           u'This field is mutually exclusive with other fields: {}',
                           len(field_names))
            raise ValidationError(msg.format(u', '.join(field_names)))


class ConfirmPassword(EqualTo):
    def __init__(self, fieldname):
        super(ConfirmPassword, self).__init__(fieldname, message=_('The passwords do not match.'))


class IndicoEmail(object):
    """Validates one or more email addresses"""
    def __init__(self, multi=False):
        self.multi = multi

    def __call__(self, form, field):
        if field.data and not is_valid_mail(field.data, self.multi):
            msg = _(u'Invalid email address list') if self.multi else _(u'Invalid email address')
            raise ValidationError(msg)


class DateTimeRange(object):
    def __init__(self, earliest=None, latest=None):
        self.earliest = earliest
        self.latest = latest

    def __call__(self, form, field):
        field_dt = as_utc(field.data)
        earliest_dt = self.get_earliest(form, field)
        latest_dt = self.get_latest(form, field)
        if field.data and field.data != field.object_data:
            if earliest_dt and field_dt < earliest_dt:
                raise ValidationError(_("Moment can't be before {}").format(format_datetime(earliest_dt)))
            if latest_dt and field_dt > latest_dt:
                raise ValidationError(_("Moment can't be after {}").format(format_datetime(latest_dt)))

    def get_earliest(self, form, field):
        earliest = self.earliest(form, field) if hasattr(self.earliest, '__call__') else self.earliest
        return as_utc(earliest) if earliest else earliest

    def get_latest(self, form, field, default_now=False):
        latest = self.latest(form, field) if hasattr(self.latest, '__call__') else self.latest
        return as_utc(latest) if latest else latest


class EarliestDateTime(DateTimeRange):
    """Validates the introduced datetime is after a given datetime or now"""

    def __init__(self, earliest=None):
        self.earliest_now = False
        super(EarliestDateTime, self).__init__(earliest=earliest)

    def __call__(self, form, field):
        earliest_dt = self.get_earliest(form, field)
        field_dt = as_utc(field.data)
        if field.data and field.data != field.object_data and field_dt < earliest_dt:
            if self.earliest_now:
                msg = _("Moment can't be in the past")
            else:
                msg = _("Moment can't be before {}").format(format_datetime(earliest_dt))
            raise ValidationError(msg)

    def get_earliest(self, form, field):
        earliest = super(EarliestDateTime, self).get_earliest(form, field)
        self.earliest_now = earliest is None
        return earliest or now_utc()


class LatestDateTime(DateTimeRange):
    """Validates the introduced datetime is before a given datetime or now"""

    def __init__(self, latest=None):
        self.latest_now = False
        super(LatestDateTime, self).__init__(latest=latest)

    def __call__(self, form, field):
        latest_dt = self.get_latest(form, field)
        field_dt = as_utc(field.data)
        if field.data and field.data != field.object_data and field_dt > latest_dt:
            if self.latest_now:
                msg = _("Moment can't be in the future")
            else:
                msg = _("Moment can't be after {}").format(format_datetime(latest_dt))
            raise ValidationError(msg)

    def get_latest(self, form, field):
        latest = super(LatestDateTime, self).get_latest(form, field)
        self.latest_now = latest is None
        return latest or now_utc()


def used_if_not_synced(form, field):
    """Validator to prevent validation error on synced inputs.

    Synced inputs are disabled in the form and don't send any value.
    In that case, we disable validation from the input.
    """
    if field.short_name in form.synced_fields:
        field.errors[:] = []
        raise StopValidation()


class UsedIfChecked(UsedIf):
    def __init__(self, field_name):
        def _condition(form, field):
            return form._fields.get(field_name).data

        super(UsedIfChecked, self).__init__(_condition)
