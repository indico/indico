# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import weakref
from collections.abc import Mapping

from flask import flash, g, has_request_context, session
from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms.csrf.core import CSRF
from wtforms.fields import FieldList
from wtforms.form import FormMeta
from wtforms.widgets.core import HiddenInput
from wtforms_sqlalchemy.fields import QuerySelectField

from indico.core import signals
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.util.string import strip_whitespace
from indico.web.util import get_request_user


class _DataWrapper:
    """Wrapper for the return value of generated_data properties."""

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f'<DataWrapper({self.data!r})>'


class generated_data(property):  # noqa: N801
    """Property decorator for generated data in forms."""

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError('unreadable attribute')
        return _DataWrapper(self.fget(obj))


class IndicoFormMeta(FormMeta):
    def __call__(cls, *args, **kwargs):  # noqa: N805
        # If we are instantiating a form that was just extended, don't
        # send the signal again - it's pointless to extend the extended
        # form and doing so could actually result in infinite recursion
        # if the signal receiver didn't specify a sender.
        if kwargs.pop('__extended', False):
            return super().__call__(*args, **kwargs)
        extra_fields = values_from_signal(signals.core.add_form_fields.send(cls, form_args=args, form_kwargs=kwargs))
        # If there are no extra fields, we don't need any custom logic
        # and simply create an instance of the original form.
        if not extra_fields:
            return super().__call__(*args, **kwargs)
        kwargs['__extended'] = True
        ext_cls = type('_Extended' + cls.__name__, (cls,), {})
        for name, field in extra_fields:
            name = 'ext__' + name
            if hasattr(ext_cls, name):
                raise RuntimeError(f'Field name collision in {cls.__name__}: {name}')
            setattr(ext_cls, name, field)
        return ext_cls(*args, **kwargs)


class IndicoFormCSRF(CSRF):
    def generate_csrf_token(self, csrf_token_field):
        return session.csrf_token

    def validate_csrf_token(self, form, field):
        if field.current_token == field.data:
            return
        if not g.get('flashed_csrf_message'):
            # Only flash the message once per request. We may end up in here
            # multiple times if `validate()` is called more than once
            flash(_('It looks like there was a problem with your current session. Please submit the form again.'),
                  'error')
            g.flashed_csrf_message = True
        raise ValidationError(_('Invalid CSRF token'))


class IndicoForm(FlaskForm, metaclass=IndicoFormMeta):
    class Meta:
        csrf = True
        csrf_class = IndicoFormCSRF

        def bind_field(self, form, unbound_field, options):
            # We don't set default filters for query-based fields as it breaks them if no query_factory is set
            # while the Form is instantiated. Also, it's quite pointless for those fields...
            # FieldList simply doesn't support filters.
            no_filter_fields = (QuerySelectField, FieldList)
            filters = [strip_whitespace] if not issubclass(unbound_field.field_class, no_filter_fields) else []
            filters += unbound_field.kwargs.get('filters', [])
            bound = unbound_field.bind(form=form, filters=filters, **options)
            bound.get_form = weakref.ref(form)  # GC won't collect the form if we don't use a weakref
            return bound

    def __init__(self, *args, **kwargs):
        csrf_enabled = kwargs.pop('csrf_enabled', None)
        if has_request_context() and get_request_user()[1] in ('oauth', 'signed_url'):
            # no csrf checks needed since oauth/token/signature auth requires a secret that's not available
            # to a malicious site, and even if it was, they wouldn't have to use CSRF to abuse it.
            csrf_enabled = False

        if csrf_enabled is not None:
            # This is exactly what FlaskForm already does, but without
            # a deprecation warning.
            # Being able to set ``csrf_enabled=False`` is much nicer
            # than ``meta={'csrf': False}`` and if we ever need to
            # change it for some reason we can always replace it everywhere
            kwargs['meta'] = kwargs.get('meta') or {}
            kwargs['meta'].setdefault('csrf', csrf_enabled)
        super().__init__(*args, **kwargs)

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators=extra_validators)
        if not valid:
            return False
        if not all(values_from_signal(signals.core.form_validated.send(self), single_value=True)):
            return False
        self.post_validate()
        return True

    def post_validate(self):
        """Called after the form was successfully validated.

        This method is a good place e.g. to override the data of fields in
        certain cases without going through the hassle of generated_data.
        """

    def populate_obj(self, obj, fields=None, skip=None, existing_only=False):
        """Populate the given object with form data.

        If `fields` is set, only fields from that list are populated.
        If `skip` is set, fields in that list are skipped.
        If `existing_only` is True, only attributes that already exist on `obj` are populated.

        Attributes starting with ``ext__`` are always skipped as they
        are from plugin-defined fields which should always be handled
        separately.
        """
        def _included(field_name):
            if fields and field_name not in fields:
                return False
            if skip and field_name in skip:
                return False
            if existing_only and not hasattr(obj, field_name):
                return False
            if field_name.startswith('ext__'):
                return False
            return True

        # Populate data from actual fields
        for name, field in self._fields.items():
            if not _included(name):
                continue
            field.populate_obj(obj, name)

        # Populate generated data
        for name, value in self.generated_data.items():
            if not _included(name):
                continue
            setattr(obj, name, value)

    @property
    def visible_fields(self):
        """A list containing all fields that are not hidden."""
        return [field for field in self if not isinstance(field.widget, HiddenInput)]

    @property
    def error_list(self):
        """A list containing all errors, prefixed with the field's label."""
        all_errors = []
        for field_name, errors in self.errors.items():
            for error in errors:
                if isinstance(error, dict) and isinstance(self[field_name], FieldList):
                    for field in self[field_name].entries:
                        all_errors += [f'{self[field_name].label.text}: {sub_error}'
                                       for sub_error in field.form.error_list]
                else:
                    all_errors.append(f'{self[field_name].label.text}: {error}')
        return all_errors

    @property
    def generated_data(self):
        """Return a dict containing all generated data."""
        cls = type(self)
        return {field: getattr(self, field).data
                for field in dir(cls)
                if isinstance(getattr(cls, field), generated_data)}

    @property
    def data(self):
        """Extend form.data with generated data from properties."""
        data = {k: v
                for k, v in super().data.items()
                if k != self.meta.csrf_field_name and not k.startswith('ext__')}
        data.update(self.generated_data)
        return data


class FormDefaults:
    """Simple wrapper to be used for Form(obj=...) default values.

    It allows you to specify default values via kwargs or certain attrs from an object.
    You can also set attributes directly on this object, which will act just like kwargs

    :param obj: The object to get data from
    :param attrs: Set of attributes that may be taken from obj
    :param skip_attrs: Set of attributes which are never taken from obj
    :param defaults: Additional values which are used only if not taken from obj
    """

    def __init__(self, obj=None, attrs=None, skip_attrs=None, **defaults):
        self.__obj = obj
        self.__use_items = isinstance(obj, Mapping)
        self.__obj_attrs = attrs
        self.__obj_attrs_skip = skip_attrs
        self.__defaults = defaults

    def __valid_attr(self, name):
        """Check if an attr may be retrieved from the object."""
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
        if key.startswith(f'_{type(self).__name__}__'):
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

    def __contains__(self, item):
        return hasattr(self, item)
