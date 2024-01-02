# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.management.views import WPEventManagement


class WPManagePersons(WPEventManagement):
    template_prefix = 'events/persons/'
    sidemenu_option = 'persons'
    bundles = ('module_events.persons.js',)
