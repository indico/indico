"""Add tags to reminder

Revision ID: f2518f111aa7
Revises: a5b6d7237997
Create Date: 2025-04-12 23:08:57.532639
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f2518f111aa7'
down_revision = 'a5b6d7237997'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('reminders_forms',
        sa.Column('reminder_id', sa.Integer(), nullable=False, index=True),
        sa.Column('reminder_form_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['reminder_id'], ['events.reminders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reminder_form_id'], ['event_registration.forms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('reminder_id', 'reminder_form_id'),
        schema='events'
    )
    op.create_table('reminders_tags',
        sa.Column('reminder_id', sa.Integer(), nullable=False, index=True),
        sa.Column('reminder_tag_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['reminder_id'], ['events.reminders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reminder_tag_id'], ['event_registration.tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('reminder_id', 'reminder_tag_id'),
        schema='events'
    )
    op.add_column('reminders',
                  sa.Column('all_tags', sa.Boolean(), nullable=False, server_default='false'),
                  schema='events')
    op.alter_column('reminders', 'all_tags', server_default=None, schema='events')


def downgrade():
    op.drop_column('reminders', 'all_tags', schema='events')
    op.drop_table('reminders_tags', schema='events')
    op.drop_table('reminders_forms', schema='events')
