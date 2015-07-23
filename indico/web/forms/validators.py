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

from wtforms.validators import StopValidation, ValidationError, EqualTo

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
        if self.condition in {True, False}:
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


def used_if_not_synced(form, field):
    """Validator to prevent validation error on synced inputs.

    Synced inputs are disabled in the form and don't send any value.
    In that case, we disable validation from the input.
    """
    if field.short_name in form.synced_fields:
        field.errors[:] = []
        raise StopValidation()
