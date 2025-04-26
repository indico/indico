"""Add tags to reminder

Revision ID: f2518f111aa7
Revises: 281d849bc4df
Create Date: 2025-04-12 23:08:57.532639
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision = 'f2518f111aa7'
down_revision = '281d849bc4df'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('reminders_tags',
        sa.Column('reminder_id', sa.Integer(), nullable=False, index=True),
        sa.Column('registration_tag_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['reminder_id'], ['events.reminders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['registration_tag_id'], ['event_registration.tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('reminder_id', 'registration_tag_id'),
        schema='events'
    )
    op.add_column('reminders', sa.Column('all_tags', sa.Boolean(), nullable=False, server_default='false'),
                  schema='events')
    op.alter_column('reminders', 'all_tags', server_default=None, schema='events')
    op.add_column('reminders',
                  sa.Column('registration_form_ids', ARRAY(sa.Integer()), nullable=False, server_default='{}'),
                  schema='events')
    op.alter_column('reminders', 'registration_form_ids', server_default=None, schema='events')


def downgrade():
    op.drop_column('reminders', 'registration_form_ids', schema='events')
    op.drop_column('reminders', 'all_tags', schema='events')
    op.drop_table('reminders_tags', schema='events')
