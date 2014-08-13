"""Use schemas

Revision ID: 9a8776f2ec2
Revises: 1adcf9d3dc7
Create Date: 2014-08-12 16:41:53.781645
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.ddl import CreateSchema, DropSchema


# revision identifiers, used by Alembic.
revision = '9a8776f2ec2'
down_revision = '1adcf9d3dc7'

schema_mapping = {'indico': ('settings',),
                  'roombooking': ('aspects', 'blocked_rooms', 'blocking_principals', 'blockings', 'equipment_types',
                                  'holidays', 'locations', 'photos', 'reservation_edit_logs', 'reservation_equipment',
                                  'reservation_occurrences', 'reservations', 'room_attributes', 'room_bookable_hours',
                                  'room_equipment', 'room_nonbookable_periods', 'rooms',
                                  'rooms_attributes_association')}


def _set_schema(table, schema, old_schema='public'):
    op.execute(sa.text('''ALTER TABLE "{}"."{}" SET SCHEMA "{}"'''.format(old_schema, table, schema)))


def upgrade():
    for schema in schema_mapping:
        op.execute(CreateSchema(schema))
    for schema, tables in schema_mapping.iteritems():
        for table in tables:
            _set_schema(table, schema)


def downgrade():
    for schema, tables in schema_mapping.iteritems():
        for table in tables:
            _set_schema(table, 'public', old_schema=schema)
    for schema in schema_mapping:
        op.execute(DropSchema(schema))
