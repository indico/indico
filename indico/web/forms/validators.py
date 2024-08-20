# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from datetime import date, timedelta
from urllib.parse import urlsplit

from wtforms.validators import EqualTo, Length, Regexp, StopValidation, ValidationError

from indico.modules.events.settings import data_retention_settings
from indico.modules.users.util import get_mastodon_server_name
from indico.util.date_time import as_utc, format_date, format_datetime, format_human_timedelta, format_time, now_utc
from indico.util.i18n import _, ngettext
from indico.util.passwords import validate_secure_password
from indico.util.string import has_relative_links, is_valid_mail


class UsedIf:
    """Make a WTF field "used" if a given condition evaluates to True.

    If the field is not used, validation stops.
    """

    field_flags = {'conditional': True}

    def __init__(self, condition):
        self.condition = condition

    def __call__(self, form, field):
        if self.condition in (True, False):
            if not self.condition:
                field.errors[:] = []
                raise StopValidation
        elif not self.condition(form, field):
            field.errors[:] = []
            raise StopValidation


class HiddenUnless:
    """Hide and disable a field unless another field has a certain value.

    :param field: The name of the other field to check
    :param value: The value to check for.  If unspecified, any truthy
                  value is accepted.
    :param preserve_data: If True, a disabled field will keep whatever
                          ``object_data`` it had before (i.e. data set
                          via `FormDefaults`).
    """

    field_flags = {'initially_hidden': True}

    def __init__(self, field, value=None, preserve_data=False):
        self.field = field
        self.value = value if value is None or isinstance(value, (set, list, tuple)) else {value}
        self.preserve_data = preserve_data

    def __call__(self, form, field):
        value = form[self.field].data
        active = (value and self.value is None) or (self.value is not None and value in self.value)

        if not active:
            field.errors[:] = []
            if field.raw_data:
                raise ValidationError('Received data for disabled field')
            if not self.preserve_data:
                # Clear existing data and use field default empty value
                field.data = None
                field.process_formdata([])
            else:
                # Clear existing data (just in case) and use the existing data for the field
                field.data = None
                field.process_data(field.object_data)
            raise StopValidation


class Exclusive:
    """Make a WTF field mutually exclusive with other fields.

    If any of the given fields have a value, the validated field may not have one.

    :param fields: names of exclusive fields
    :param strict: whether to check for none instead of falsiness
    :param message: a custom message for the validation error
    """

    def __init__(self, *fields, strict=True, message=None):
        self.fields = fields
        self.strict = strict
        self.message = message

    def _is_value(self, value):
        return (value is not None) if self.strict else bool(value)

    def __call__(self, form, field):
        if not self._is_value(field.data):
            return
        if any(self._is_value(form[f].data) for f in self.fields):
            if self.message:
                raise ValidationError(self.message)
            field_names = sorted(str(form[f].label.text) for f in self.fields)
            msg = ngettext('This field is mutually exclusive with another field: {}',
                           'This field is mutually exclusive with other fields: {}',
                           len(field_names))
            raise ValidationError(msg.format(', '.join(field_names)))


class ConfirmPassword(EqualTo):
    def __init__(self, fieldname):
        super().__init__(fieldname, message=_('The passwords do not match.'))


class IndicoEmail:
    """Validate one or more email addresses."""

    def __init__(self, multi=False):
        self.multi = multi

    def __call__(self, form, field):
        if field.data and not is_valid_mail(field.data, self.multi):
            msg = _('Invalid email address list') if self.multi else _('Invalid email address')
            raise ValidationError(msg)


class DateRange:
    """Validate that a date is within the specified boundaries."""

    field_flags = {'date_range': True}

    def __init__(self, earliest='today', latest=None):
        self.earliest = earliest
        self.latest = latest
        # set to true in get_earliest/get_latest if applicable
        self.earliest_today = False
        self.latest_today = False

    def __call__(self, form, field):
        if field.data is None:
            return
        field_date = field.data
        earliest_date = self.get_earliest(form, field)
        latest_date = self.get_latest(form, field)
        if field_date != field.object_data:
            if earliest_date and field_date < earliest_date:
                if self.earliest_today:
                    msg = _("'{}' can't be in the past").format(field.label)
                else:
                    msg = _("'{}' can't be before {}").format(field.label, format_date(earliest_date))
                raise ValidationError(msg)
            if latest_date and field_date > latest_date:
                if self.latest_today:
                    msg = _("'{}' can't be in the future").format(field.label)
                else:
                    msg = _("'{}' can't be after {}").format(field.label, format_date(latest_date))
                raise ValidationError(msg)

    def get_earliest(self, form, field):
        earliest = self.earliest(form, field) if callable(self.earliest) else self.earliest
        if earliest == 'today':
            self.earliest_today = True
            return date.today()
        return earliest

    def get_latest(self, form, field):
        latest = self.latest(form, field) if callable(self.latest) else self.latest
        if latest == 'today':
            self.latest_today = True
            return date.today()
        return latest


class DateTimeRange:
    """Validate that a datetime is within the specified boundaries."""

    field_flags = {'datetime_range': True}

    def __init__(self, earliest='now', latest=None):
        self.earliest = earliest
        self.latest = latest
        # set to true in get_earliest/get_latest if applicable
        self.earliest_now = False
        self.latest_now = False

    def __call__(self, form, field):
        if field.data is None:
            return
        field_dt = as_utc(field.data)
        earliest_dt = self.get_earliest(form, field)
        latest_dt = self.get_latest(form, field)
        if field_dt != field.object_data:
            if earliest_dt and field_dt < earliest_dt:
                if self.earliest_now:
                    msg = _("'{}' can't be in the past ({})").format(field.label, field.timezone)
                else:
                    dt = format_datetime(earliest_dt, timezone=field.timezone)
                    msg = _("'{}' can't be before {} ({})").format(field.label, dt, field.timezone)
                raise ValidationError(msg)
            if latest_dt and field_dt > latest_dt:
                if self.latest_now:
                    msg = _("'{}' can't be in the future ({})").format(field.label, field.timezone)
                else:
                    dt = format_datetime(latest_dt, timezone=field.timezone)
                    msg = _("'{}' can't be after {} ({})").format(field.label, dt, field.timezone)
                raise ValidationError(msg)

    def get_earliest(self, form, field):
        earliest = self.earliest(form, field) if callable(self.earliest) else self.earliest
        if earliest == 'now':
            self.earliest_now = True
            return now_utc().replace(second=0, microsecond=0)
        return as_utc(earliest) if earliest else earliest

    def get_latest(self, form, field):
        latest = self.latest(form, field) if callable(self.latest) else self.latest
        if latest == 'now':
            self.latest_now = True
            return now_utc().replace(second=59, microsecond=999)
        return as_utc(latest) if latest else latest


class LinkedDate:
    """Validate that a date field happens before or/and after another.

    If both ``not_before`` and ``not_after`` are set to ``True``, both fields have to
    be equal.
    """

    field_flags = {'linked_date': True}

    def __init__(self, field, not_before=True, not_after=False, not_equal=False):
        if not not_before and not not_after:
            raise ValueError('Invalid validation')
        self.not_before = not_before
        self.not_after = not_after
        self.not_equal = not_equal
        self.linked_field = field

    def __call__(self, form, field):
        if field.data is None:
            return
        linked_field = form[self.linked_field]
        if linked_field.data is None:
            return
        linked_field_date = linked_field.data
        field_date = field.data
        if self.not_before and field_date < linked_field_date:
            raise ValidationError(_("{} can't be before {}").format(field.label, linked_field.label))
        if self.not_after and field_date > linked_field_date:
            raise ValidationError(_("{} can't be after {}").format(field.label, linked_field.label))
        if self.not_equal and field_date == linked_field_date:
            raise ValidationError(_("{} can't be equal to {}").format(field.label, linked_field.label))


class LinkedDateTime:
    """Validate that a datetime field happens before or/and after another.

    If both ``not_before`` and ``not_after`` are set to ``True``, both fields have to
    be equal.
    """

    field_flags = {'linked_datetime': True}

    def __init__(self, field, not_before=True, not_after=False, not_equal=False):
        if not not_before and not not_after:
            raise ValueError('Invalid validation')
        self.not_before = not_before
        self.not_after = not_after
        self.not_equal = not_equal
        self.linked_field = field

    def __call__(self, form, field):
        if field.data is None:
            return
        linked_field = form[self.linked_field]
        if linked_field.data is None:
            return
        linked_field_dt = as_utc(linked_field.data)
        field_dt = as_utc(field.data)
        if self.not_before and field_dt < linked_field_dt:
            raise ValidationError(_("{} can't be before {}").format(field.label, linked_field.label))
        if self.not_after and field_dt > linked_field_dt:
            raise ValidationError(_("{} can't be after {}").format(field.label, linked_field.label))
        if self.not_equal and field_dt == linked_field_dt:
            raise ValidationError(_("{} can't be equal to {}").format(field.label, linked_field.label))


class UsedIfChecked(UsedIf):
    def __init__(self, field_name):
        def _condition(form, field):
            return form._fields.get(field_name).data

        super().__init__(_condition)


class MaxDuration:
    """Validate the duration doesn't exceed `max_duration`."""

    def __init__(self, max_duration=None, **kwargs):
        assert max_duration or kwargs
        assert max_duration is None or not kwargs
        self.max_duration = max_duration if max_duration is not None else timedelta(**kwargs)

    def __call__(self, form, field):
        if field.data is not None and field.data > self.max_duration:
            raise ValidationError(_('Duration cannot exceed {}').format(format_human_timedelta(self.max_duration)))


class TimeRange:
    """Validate the time lies within boundaries."""

    def __init__(self, earliest=None, latest=None):
        assert earliest is not None or latest is not None, 'At least one of `earliest` or `latest` must be specified.'
        if earliest is not None and latest is not None:
            assert earliest <= latest, '`earliest` cannot be later than `latest`.'
        self.earliest = earliest
        self.latest = latest

    def __call__(self, form, field):
        def _format_time(value):
            return format_time(value) if value else None
        if (self.earliest and field.data < self.earliest) or (self.latest and field.data > self.latest):
            if self.earliest is not None and self.latest is not None:
                message = _('Must be between {earliest} and {latest}.')
            elif self.latest is None:
                message = _('Must be later than {earliest}.')
            else:
                message = _('Must be earlier than {latest}.')
        raise ValidationError(message.format(earliest=_format_time(self.earliest), latest=_format_time(self.latest)))


class WordCount:
    """Validate the word count of a string.

    :param min: The minimum number of words in the string.  If not
                provided, the minimum word count will not be checked.
    :param min: The maximum number of words in the string.  If not
                provided, the maximum word count will not be checked.
    """

    def __init__(self, min=-1, max=-1):
        assert min != -1 or max != -1, 'At least one of `min` or `max` must be specified.'
        assert max == -1 or min <= max, '`min` cannot be more than `max`.'
        self.min = min
        self.max = max

    def __call__(self, form, field):
        count = len(re.split(r'\s+', field.data, flags=re.UNICODE)) if field.data else 0
        if count < self.min or (self.max != -1 and count > self.max):
            if self.max == -1:
                message = ngettext('Field must contain at least {min} word.',
                                   'Field must contain at least {min} words.', self.min)
            elif self.min == -1:
                message = ngettext('Field cannot contain more than {max} word.',
                                   'Field cannot contain more than {max} words.', self.max)
            else:
                message = _('Field must contain between {min} and {max} words.')
            raise ValidationError(message.format(min=self.min, max=self.max, length=count))


class IndicoRegexp(Regexp):
    """
    Like the WTForms `Regexp` validator, but supports populating the
    HTML5 `patttern` attribute (the regex may not use any non-standard
    Python extensions such as named groups in this case).
    """

    def __init__(self, *args, **kwargs):
        self.client_side = kwargs.pop('client_side', True)
        super().__init__(*args, **kwargs)


class SoftLength(Length):
    """
    Like the WTForms `Length` validator, but allows typing beyond the
    limit and just fails validation once the limit has been exceeded.

    The client-side implementation also skips leading/trailing
    whitespace which is in line with the behavior in all our forms
    where surrounding whitespace is stripped before validation.
    """

    def __call__(self, form, field):
        orig_data = field.data
        if field.data is not None:
            field.data = re.sub(r'(\r\n|\r)', '\n', field.data)
        try:
            super().__call__(form, field)
        finally:
            field.data = orig_data


class SecurePassword:
    """Validate that a string is a secure password."""

    # This is only defined here so the `_attrs_for_validators` util does
    # not need to hard-code it.
    MIN_LENGTH = 8

    def __init__(self, context='wtforms-field', username_field=None):
        self.context = context
        self.username_field = username_field

    def __call__(self, form, field):
        username = ''
        if self.username_field:
            username = form[self.username_field].data or ''
        password = field.data or ''
        if error := validate_secure_password(self.context, password, username=username):
            raise ValidationError(error)


class NoRelativeURLs:
    """Validate that an HTML strings contains no relative URLs.

    This checks only ``img[src]`` and ``a[href]``, but not URLs present as plain
    text or in any other (unexpected) places.
    """

    def __call__(self, form, field):
        if field.data and has_relative_links(field.data):
            raise ValidationError(_('Links and images may not use relative URLs.'))


class MastodonServer:
    """Check that a given URL is a valid Mastodon server URL."""

    def __call__(self, form, field):
        if field.data:
            url = urlsplit(field.data)
            if url.scheme not in ('http', 'https'):
                raise ValidationError(_('Invalid URL.'))

            if not get_mastodon_server_name(field.data):
                raise ValidationError(_('Invalid Mastodon server URL.'))


class DataRetentionPeriodValidator:
    """Validate a data retention period against the global defaults."""

    def __call__(self, form, field):
        retention_period = field.data
        max_retention_period = data_retention_settings.get('maximum_data_retention')
        if max_retention_period and retention_period is None:
            raise ValidationError(_('The retention period cannot be indefinite.'))
        elif retention_period is None:
            return
        min_retention_period = data_retention_settings.get('minimum_data_retention')
        if retention_period < min_retention_period:
            raise ValidationError(ngettext('The retention period cannot be less than {} week.',
                                           'The retention period cannot be less than {} weeks.',
                                           min_retention_period.days // 7)
                                  .format(min_retention_period.days // 7))
        elif max_retention_period and retention_period > max_retention_period:
            raise ValidationError(ngettext('The retention period cannot be longer than {} week.',
                                           'The retention period cannot be longer than {} weeks.',
                                           max_retention_period.days // 7)
                                  .format(max_retention_period.days // 7))
        elif not max_retention_period and retention_period > timedelta(3650):
            raise ValidationError(_('The retention period cannot be longer than 10 years. Leave the field empty for '
                                    'indefinite.'))
