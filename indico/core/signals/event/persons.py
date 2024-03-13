# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.signals.event import _signals


person_updated = _signals.signal('person-updated', '''
Called when an EventPerson is modified. The *sender* is the EventPerson.
''')

person_link_field_extra_params = _signals.signal('person-link-field-extra-params', '''
The signal should return a dict containing extra parameters that will be passed to
the PersonLinkFields. The *sender* is the field.

The parameter `disable_affiliations` can be used to disable the affiliations
field in the person details modal.

All parameters are camelized and passed to the `personListItemActions` and
`personLinkFieldModals` React hooks.
''')
