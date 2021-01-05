# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement


class WPEditing(WPEventManagement):
    template_prefix = 'events/editing/'
    sidemenu_option = 'editing'
    # TODO: remove mathjax later on from here (it is just here to make the timeline work)
    bundles = ('module_events.editing.js', 'module_events.editing.css', 'mathjax.js')


class WPEditingView(WPEditing):
    MANAGEMENT = False
