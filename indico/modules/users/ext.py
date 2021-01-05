# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals


class ExtraUserPreferences(object):
    """Define additional user preferences.

    To use this class, subclass it and override `defaults`,
    `fields` and `save` to implement your custom logic.
    """

    _prefix = 'extra_'
    #: a dict containing all the fields that should be added to the user preferences
    fields = {}

    def __init__(self, user):
        self.user = user

    @classmethod
    def is_active(cls, user):
        """Return whether the preferences are available for the given user."""
        return True

    def load(self):
        """Return a dict with the current values for the user."""
        raise NotImplementedError

    def save(self, data):
        """Save the updated settings."""
        raise NotImplementedError

    # All the following methods are internal and usually do not need
    # to be called/used when implementing custom settings.

    def extend_defaults(self, defaults):
        """Add values to the FormDefaults."""
        for key, value in self.load().iteritems():
            key = self._prefix + key
            if hasattr(defaults, key):
                raise RuntimeError('Preference collision: {}'.format(key))
            defaults[key] = value

    def process_form_data(self, data):
        """Process and save submitted data.

        This modifies `data` so the core code doesn't receive any extra
        data it doesn't expect.
        """
        local_data = {}
        for key in self.fields:
            local_data[key] = data.pop(self._prefix + key)
        self.save(local_data)

    def extend_form(self, form_class):
        """Create a subclass of the form containing the extra field."""
        form_class = type(b'ExtendedUserPreferencesForm', (form_class,), {})
        for name, field in self.fields.iteritems():
            name = self._prefix + name
            if hasattr(form_class, name):
                raise RuntimeError('Preference collision: {}'.format(name))
            setattr(form_class, name, field)
        return form_class
