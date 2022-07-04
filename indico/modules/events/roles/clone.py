# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner, get_attrs_to_clone
from indico.modules.events.models.events import EventType
from indico.modules.events.models.roles import EventRole
from indico.util.i18n import _


class EventRoleCloner(EventCloner):
    name = 'event_roles'
    friendly_name = _('Event roles')
    is_default = True

    @property
    def is_visible(self):
        return self.old_event.type_ == EventType.conference

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def get_conflicts(self, target_event):
        if self._has_content(target_event):
            return [_('The target event already has event roles')]

    def run(self, new_event, cloners, shared_data, event_exists):
        self._event_role_map = {}
        self._clone_event_roles(new_event)
        db.session.flush()
        return {'event_role_map': self._event_role_map}

    def _has_content(self, event):
        return bool(event.roles)

    @no_autoflush
    def _clone_event_roles(self, new_event):
        attrs = get_attrs_to_clone(EventRole, add={'members'})
        for old_event_role in self.old_event.roles:
            event_role = EventRole()
            event_role.populate_from_attrs(old_event_role, attrs)
            new_event.roles.append(event_role)
            self._event_role_map[old_event_role] = event_role
