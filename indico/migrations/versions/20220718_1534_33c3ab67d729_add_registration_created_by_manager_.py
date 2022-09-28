"""Add registration created_by_manager column

Revision ID: 33c3ab67d729
Revises: 0c4bb2973536
Create Date: 2022-07-18 15:34:10.727423
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '33c3ab67d729'
down_revision = '0c4bb2973536'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations', sa.Column('created_by_manager', sa.Boolean(), nullable=False,
                                             server_default='false'), schema='event_registration')
    op.alter_column('registrations', 'created_by_manager', server_default=None, schema='event_registration')
    op.execute('''
        UPDATE event_registration.registrations reg
        SET created_by_manager = true
        FROM events.logs lo
        WHERE
        lo.realm = 2 AND
        lo.module = 'Registration' AND
        lo.summary LIKE 'New registration: %' AND
        lo.meta ? 'registration_id' AND
        reg.id = (lo.meta -> 'registration_id')::int;
    ''')


def downgrade():
    op.drop_column('registrations', 'created_by_manager', schema='event_registration')
