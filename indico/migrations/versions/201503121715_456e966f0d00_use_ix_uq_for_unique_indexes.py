"""Use ix_uq for unique indexes

Revision ID: 456e966f0d00
Revises: 4ae6d2113a2b
Create Date: 2015-03-12 17:15:08.733374
"""

from alembic import op

from indico.core.db.sqlalchemy.util.bulk_rename import bulk_rename


# revision identifiers, used by Alembic.
revision = '456e966f0d00'
down_revision = '4ae6d2113a2b'


mapping = {
    'roombooking.locations': {
        'indexes': {
            'ix_locations_name': 'ix_uq_locations_name',
        }
    }
}


def upgrade():
    for stmt in bulk_rename(mapping):
        op.execute(stmt)


def downgrade():
    for stmt in bulk_rename(mapping, True):
        op.execute(stmt)
