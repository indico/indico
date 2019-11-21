# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.features.base import EventFeature
from indico.modules.events.models.events import EventType
from indico.util.i18n import _


logger = Logger.get('events.editing')


class EditingFeature(EventFeature):
    name = 'editing'
    friendly_name = _('Paper Editing')
    description = _('Gives event managers the opportunity to let contributors submit papers to be edited and '
                    'eventually published.')

    @classmethod
    def is_allowed_for_event(cls, event):
        return event.type_ == EventType.conference


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return EditingFeature
