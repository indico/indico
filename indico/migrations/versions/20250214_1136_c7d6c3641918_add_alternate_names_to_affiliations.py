"""Add alternate names to affiliations
Revision ID: c7d6c3641918
Revises: 9251bc3e2106
Create Date: 2025-02-14 11:36:35.560567
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c7d6c3641918'
down_revision = '9251bc3e2106'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('affiliations', sa.Column('alt_names', postgresql.ARRAY(sa.String()),
                                            nullable=False, server_default='{}'), schema='indico')
    op.alter_column('affiliations', 'alt_names', server_default=None, schema='indico')
    op.create_index(None, 'affiliations', ['alt_names'], unique=False, schema='indico')


def downgrade():
    op.drop_index('ix_affiliations_alt_names', table_name='affiliations', schema='indico')
    op.drop_column('affiliations', 'alt_names', schema='indico')
