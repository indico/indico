## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from flask_wtf import Form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.core import FieldList
from wtforms.widgets.core import HiddenInput

from indico.util.string import strip_whitespace


class _DataWrapper(object):
    """Wrapper for the return value of generated_data properties"""
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return '<DataWrapper({!r})>'.format(self.data)


class generated_data(property):
    """property decorator for generated data in forms"""

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return _DataWrapper(self.fget(obj))


class IndicoForm(Form):
    class Meta:
        def bind_field(self, form, unbound_field, options):
            # We don't set default filters for query-based fields as it breaks them if no query_factory is set
            # while the Form is instantiated. Also, it's quite pointless for those fields...
            filters = [strip_whitespace] if not issubclass(unbound_field.field_class, QuerySelectField) else []
            filters += unbound_field.kwargs.get('filters', [])
            return unbound_field.bind(form=form, filters=filters, **options)

    def populate_obj(self, obj, fields=None, skip=None, existing_only=False):
        """Populates the given object with form data.

        If `fields` is set, only fields from that list are populated.
        If `skip` is set, fields in that list are skipped.
        If `existing_only` is True, only attributes that already exist on `obj` are populated.
        """
        for name, field in self._fields.iteritems():
            if fields and name not in fields:
                continue
            if skip and name in skip:
                continue
            if existing_only and not hasattr(obj, name):
                continue
            field.populate_obj(obj, name)

    @property
    def visible_fields(self):
        """A list containing all fields that are not hidden."""
        return [field for field in self if not isinstance(field.widget, HiddenInput)]

    @property
    def error_list(self):
        """A list containing all errors, prefixed with the field's label.'"""
        all_errors = []
        for field_name, errors in self.errors.iteritems():
            for error in errors:
                if isinstance(error, dict) and isinstance(self[field_name], FieldList):
                    for field in self[field_name].entries:
                        all_errors += ['{}: {}'.format(self[field_name].label.text, sub_error)
                                       for sub_error in field.form.error_list]
                else:
                    all_errors.append('{}: {}'.format(self[field_name].label.text, error))
        return all_errors

    @property
    def data(self):
        """Extends form.data with generated data from properties"""
        data = super(IndicoForm, self).data
        cls = type(self)
        for field in dir(cls):
            if isinstance(getattr(cls, field), generated_data):
                data[field] = getattr(self, field).data
        return data


class FormDefaults(object):
    """Simple wrapper to be used for Form(obj=...) default values.

    It allows you to specify default values via kwargs or certain attrs from an object.
    You can also set attributes directly on this object, which will act just like kwargs
    """

    def __init__(self, obj=None, attrs=None, skip_attrs=None, **defaults):
        self.__obj = obj
        self.__use_items = hasattr(obj, 'iteritems') and hasattr(obj, 'get')  # smells like a dict
        self.__obj_attrs = attrs
        self.__obj_attrs_skip = skip_attrs
        self.__defaults = defaults

    def __valid_attr(self, name):
        """Checks if an attr may be retrieved from the object"""
        if self.__obj is None:
            return False
        if self.__obj_attrs is not None and name not in self.__obj_attrs:
            return False
        if self.__obj_attrs_skip is not None and name in self.__obj_attrs_skip:
            return False
        return True

    def __setitem__(self, key, value):
        self.__defaults[key] = value

    def __setattr__(self, key, value):
        if key.startswith('_{}__'.format(type(self).__name__)):
            object.__setattr__(self, key, value)
        else:
            self.__defaults[key] = value

    def __getattr__(self, item):
        if self.__valid_attr(item):
            if self.__use_items:
                return self.__obj.get(item, self.__defaults.get(item))
            else:
                return getattr(self.__obj, item, self.__defaults.get(item))
        elif item in self.__defaults:
            return self.__defaults[item]
        else:
            raise AttributeError(item)
