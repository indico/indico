# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.core.logger import Logger


logger = Logger.get('files')


@signals.core.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.files.tasks  # noqa: F401
