# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy import DDL


COLLATION_CASE_INSENSITIVE_DDL = '''
    CREATE COLLATION indico.case_insensitive (
        provider = icu,
        locale = 'und-u-ks-level2',
        deterministic = false
    )
'''


def create_case_insensitive_collation(conn):
    DDL(COLLATION_CASE_INSENSITIVE_DDL).execute(conn)
