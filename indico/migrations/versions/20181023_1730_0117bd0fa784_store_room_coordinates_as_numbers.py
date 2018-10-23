"""Store room coordinates as numbers

Revision ID: 0117bd0fa784
Revises: c5c21246445a
Create Date: 2018-10-23 17:30:19.643051
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0117bd0fa784'
down_revision = 'c5c21246445a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE roombooking.rooms SET longitude = NULL WHERE longitude = ''")
    op.execute("UPDATE roombooking.rooms SET latitude = NULL WHERE latitude = ''")
    op.alter_column('rooms', 'longitude', type_=sa.Float, schema='roombooking',
                    postgresql_using='longitude::double precision')
    op.alter_column('rooms', 'latitude', type_=sa.Float, schema='roombooking',
                    postgresql_using='latitude::double precision')


def downgrade():
    op.alter_column('rooms', 'longitude', type_=sa.String, schema='roombooking')
    op.alter_column('rooms', 'latitude', type_=sa.String, schema='roombooking')
