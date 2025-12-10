# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from alembic import context

from indico.core.db import db


version_table = os.environ.get('ALEMBIC_VERSION_TEST_DB', 'alembic_version')
context.configure(connection=context.config.attributes['connection'],
                  target_metadata=db.metadata,
                  version_table=version_table,
                  version_table_schema='public')

with context.begin_transaction():
    context.run_migrations()
