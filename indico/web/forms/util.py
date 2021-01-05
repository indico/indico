# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict
from copy import deepcopy

from wtforms.fields.core import UnboundField


def get_form_field_names(form_class):
    """Return the list of field names of a WTForm.

    :param form_class: A `Form` subclass
    """
    unbound_fields = form_class._unbound_fields
    if unbound_fields:
        return [f[0] for f in unbound_fields]
    field_names = []
    # the following logic has been taken from FormMeta.__call__
    for name in dir(form_class):
        if not name.startswith('_'):
            unbound_field = getattr(form_class, name)
            if hasattr(unbound_field, '_formfield'):
                field_names.append(name)
    return field_names


def inject_validators(form, field_name, validators, early=False):
    """Add extra validators to a form field.

    This function may be called from the ``__init__`` method of a
    form before the ``super().__init__()`` call or on a form class.
    When using a Form class note that this will modify the class, so
    all new instances of it will be affected!

    :param form: the `Form` instance or a `Form` subclass
    :param field_name: the name of the field to change
    :param validators: a list of validators to add
    :param early: whether to inject the validator before any existing
                  validators. this is needed if a field has a validator
                  that stops validation such as DataRequired and the
                  injected one is e.g. HiddenUnless which needs to run
                  even if the field is invalid
    """
    unbound = deepcopy(getattr(form, field_name))
    assert isinstance(unbound, UnboundField)
    if 'validators' in unbound.kwargs:
        if early:
            unbound.kwargs['validators'] = validators + unbound.kwargs['validators']
        else:
            unbound.kwargs['validators'] += validators
    elif len(unbound.args) > 1:
        if early:
            validators_arg = validators + unbound.args[1]
        else:
            validators_arg = unbound.args[1] + validators
        unbound.args = unbound.args[:1] + (validators_arg,) + unbound.args[2:]
    else:
        unbound.kwargs['validators'] = validators
    setattr(form, field_name, unbound)
    if form._unbound_fields is not None:
        unbound_fields = OrderedDict(form._unbound_fields)
        unbound_fields[field_name] = unbound
        form._unbound_fields = unbound_fields.items()
