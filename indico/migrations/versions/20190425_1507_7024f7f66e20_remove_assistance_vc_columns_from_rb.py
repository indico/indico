"""Remove assistance/vc columns from rb

Revision ID: 7024f7f66e20
Revises: a83e77e11e36
Create Date: 2019-04-25 15:07:20.614620
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '7024f7f66e20'
down_revision = 'a83e77e11e36'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('reservations', 'needs_vc_assistance', schema='roombooking')
    op.drop_column('reservations', 'uses_vc', schema='roombooking')
    op.drop_column('reservations', 'needs_assistance', schema='roombooking')
    op.drop_column('rooms', 'notification_for_assistance', schema='roombooking')


def downgrade():
    op.add_column('rooms',
                  sa.Column('notification_for_assistance', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.add_column('reservations',
                  sa.Column('needs_assistance', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.add_column('reservations',
                  sa.Column('uses_vc', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.add_column('reservations',
                  sa.Column('needs_vc_assistance', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.alter_column('rooms', 'notification_for_assistance', server_default=None, schema='roombooking')
    op.alter_column('reservations', 'needs_assistance', server_default=None, schema='roombooking')
    op.alter_column('reservations', 'uses_vc', server_default=None, schema='roombooking')
    op.alter_column('reservations', 'needs_vc_assistance', server_default=None, schema='roombooking')
