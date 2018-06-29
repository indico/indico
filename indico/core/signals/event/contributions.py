# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.signals.event import _signals


contribution_created = _signals.signal('contribution-created', """
Called when a new contribution is created. The `sender` is the new contribution.
""")

contribution_deleted = _signals.signal('contribution-deleted', """
Called when a contribution is deleted. The *sender* is the contribution.
""")

contribution_updated = _signals.signal('contribution-updated', """
Called when a contribution is modified. The *sender* is the contribution.
A dict containing ``old, new`` tuples for all changed values is passed
in the ``changes`` kwarg.
""")


subcontribution_created = _signals.signal('subcontribution-created', """
Called when a new subcontribution is created. The `sender` is the new subcontribution.
""")

subcontribution_deleted = _signals.signal('subcontribution-deleted', """
Called when a subcontribution is deleted. The *sender* is the subcontribution.
""")

subcontribution_updated = _signals.signal('subcontribution-updated', """
Called when a subcontribution is modified. The *sender* is the subcontribution.
""")

get_export_formats = _signals.signal('get-export-formats', """
Called to get available export formats, expects a list of (key, display string, callable, opts)
as return values. The callable should accept (event, contribs, sort_by, opts) as arguments and should
return the final export data via send_file or similar.
""")
