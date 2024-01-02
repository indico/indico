# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.fields import PersonLinkListFieldBase
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.web.forms.widgets import JinjaWidget


class SessionBlockPersonLinkListField(PersonLinkListFieldBase):
    person_link_cls = SessionBlockPersonLink
    linked_object_attr = 'session_block'
    widget = JinjaWidget('forms/person_link_widget.html')

    def _serialize_person_link(self, principal):
        from indico.modules.events.persons.schemas import PersonLinkSchema
        return PersonLinkSchema().dump(principal)
