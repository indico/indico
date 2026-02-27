# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


affiliation_created = _signals.signal('affiliation-created', '''
Called from RHAffiliationAPI when processing new affiliations. The *sender* is the
Affiliation being created.
''')

affiliation_updated = _signals.signal('affiliation-updated', '''
Called from RHAffiliationAPI when processing updates. The *sender* is the
Affiliation being updated and the update dict is passed via ``payload``.
''')

get_affiliation_filters = _signals.signal('get-affiliation-filters', '''
Called when searching and validating affiliations in an affiliations field. The
*sender* is the object from which affiliations are filtered. The current context
is passed via ``context``. Expected to return a list of SQLAlchemy filters to
restrict results.
''')
