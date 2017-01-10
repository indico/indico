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

from __future__ import unicode_literals

import weakref

from flask import request, session, flash, g
from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.core import FieldList
from wtforms.form import FormMeta
from wtforms.widgets.core import HiddenInput

from indico.core import signals
from indico.core.auth import multipass
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.util.string import strip_whitespace, return_ascii
from indico.web.flask.util import url_for


class _DataWrapper(object):
    """Wrapper for the return value of generated_data properties"""
    def __init__(self, data):
        self.data = data

    @return_ascii
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


class IndicoFormMeta(FormMeta):
    def __call__(cls, *args, **kwargs):
        # If we are instantiating a form that was just extended, don't
        # send the signal again - it's pointless to extend the extended
        # form and doing so could actually result in infinite recursion
        # if the signal receiver didn't specify a sender.
        if kwargs.pop('__extended', False):
            return super(IndicoFormMeta, cls).__call__(*args, **kwargs)
        extra_fields = values_from_signal(signals.add_form_fields.send(cls))
        # If there are no extra fields, we don't need any custom logic
        # and simply create an instance of the original form.
        if not extra_fields:
            return super(IndicoFormMeta, cls).__call__(*args, **kwargs)
        kwargs['__extended'] = True
        ext_cls = type(b'_Extended' + cls.__name__, (cls,), {})
        for name, field in extra_fields:
            name = 'ext__' + name
            if hasattr(ext_cls, name):
                raise RuntimeError('Preference collision in {}: {}'.format(cls.__name__, name))
            setattr(ext_cls, name, field)
        return ext_cls(*args, **kwargs)


class IndicoForm(FlaskForm):
    __metaclass__ = IndicoFormMeta

    class Meta:
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
        super(IndicoForm, self).__init__(*args, **kwargs)
        self.ajax_response = None

    def process_ajax(self):
        """
        Check if the current request is an AJAX request related to a
        field in this form and execute the field's AJAX logic.

        The response is available in the `ajax_response` attribute
        afterwards.

        :return: Whether an AJAX response was processed.
        """
        field_id = request.args.get('__wtf_ajax')
        if not field_id:
            return False
        field = next((f for f in self._fields.itervalues() if f.id == field_id and isinstance(f, AjaxFieldMixin)), None)
        if not field:
            return False
        rv = field.process_ajax()
        self.ajax_response = rv
        return True

    def generate_csrf_token(self, csrf_context=None):
        if not self.csrf_enabled:
            return None
        return session.csrf_token

    def validate_csrf_token(self, field):
        if self.csrf_enabled and field.data != session.csrf_token:
            if not g.get('flashed_csrf_message'):
                # Only flash the message once per request. We may end up in here
                # multiple times if `validate()` is called more than once
                flash(_('It looks like there was a problem with your current session. Please submit the form again.'),
                      'error')
                g.flashed_csrf_message = True
            raise ValidationError(_('CSRF token missing'))

    def validate(self):
        valid = super(IndicoForm, self).validate()
        if not valid:
            return False
        if not all(values_from_signal(signals.form_validated.send(self), single_value=True)):
            return False
        self.post_validate()
        return True

    def post_validate(self):
        """Called after the form was successfully validated.

        This method is a good place e.g. to override the data of fields in
        certain cases without going through the hassle of generated_data.
        """

    def populate_obj(self, obj, fields=None, skip=None, existing_only=False):
        """Populates the given object with form data.

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
        for name, field in self._fields.iteritems():
            if not _included(name):
                continue
            field.populate_obj(obj, name)

        # Populate generated data
        for name, value in self.generated_data.iteritems():
            if not _included(name):
                continue
            setattr(obj, name, value)

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
    def generated_data(self):
        """Returns a dict containing all generated data"""
        cls = type(self)
        return {field: getattr(self, field).data
                for field in dir(cls)
                if isinstance(getattr(cls, field), generated_data)}

    @property
    def data(self):
        """Extends form.data with generated data from properties"""
        data = {k: v for k, v in super(IndicoForm, self).data.iteritems() if not k.startswith('ext__')}
        data.update(self.generated_data)
        return data


class FormDefaults(object):
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

    def __contains__(self, item):
        return hasattr(self, item)


class SyncedInputsMixin(object):
    """Mixin for a form having inputs using the ``SyncedInputWidget``.

    This mixin will process the synced fields, adding them the necessary
    attributes for them to render and work properly.  The fields which
    are synced are defined by ``multipass.synced_fields``.

    :param synced_fields: set -- a subset of ``multipass.synced_fields``
                          which corresponds to the fields currently
                          being synchronized for the user.
    :param synced_values: dict -- a map of all the synced fields (as
                          defined by ``multipass.synced_fields``) and
                          the values they would have if they were synced
                          (regardless of whether it is or not).  Fields
                          not present in this dict do not show the sync
                          button at all.
    """

    def __init__(self, *args, **kwargs):
        synced_fields = kwargs.pop('synced_fields', set())
        synced_values = kwargs.pop('synced_values', {})
        super(SyncedInputsMixin, self).__init__(*args, **kwargs)
        self.syncable_fields = set(synced_values)
        for key in ('first_name', 'last_name'):
            if not synced_values.get(key):
                synced_values.pop(key, None)
                self.syncable_fields.discard(key)
        if self.is_submitted():
            synced_fields = self.synced_fields
        provider = multipass.sync_provider
        provider_name = provider.title if provider is not None else 'unknown identity provider'
        for field in multipass.synced_fields:
            self[field].synced = self[field].short_name in synced_fields
            self[field].synced_value = synced_values.get(field)
            self[field].provider_name = provider_name

    @property
    def synced_fields(self):
        """The fields which are set as synced for the current request."""
        return set(request.form.getlist('synced_fields')) & self.syncable_fields


class AjaxFieldMixin(object):
    """Mixin for a Field to be able to handle AJAX requests.

    This mixin will allow you to handle AJAX requests during regular
    form processing, e.g. when you have a field that needs an AJAX
    callback to perform search operations.

    To use this mixin, the controllers processing the form must
    include the following code::

        if form.process_ajax():
            return form.ajax_response

    It is a good idea to run this code as early as possible to avoid
    doing expensive operations like loading a big list of objects
    which may be never used when returning early due to the AJAX
    request.
    """

    def process_ajax(self):
        raise NotImplementedError

    def get_ajax_url(self, **url_args):
        kwargs = dict(request.view_args, **request.args.to_dict(False))
        kwargs.update(url_args)
        kwargs['__wtf_ajax'] = self.id
        return url_for(request.endpoint, **kwargs)
