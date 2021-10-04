"""Add registration tags

Revision ID: b36825c7869e
Revises: dc53d6e8c576
Create Date: 2021-09-27 10:27:39.335488
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b36825c7869e'
down_revision = 'dc53d6e8c576'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_registration'
    )

    op.create_index('ix_uq_tags_title_lower', 'tags', ['event_id', sa.text('lower(title)')],
                    unique=True, schema='event_registration')

    # Many-to-many table between registrations and tags
    op.create_table(
        'registration_tags',
        sa.Column('registration_id', sa.Integer(), nullable=False, index=True),
        sa.Column('registration_tag_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['registration_id'], ['event_registration.registrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['registration_tag_id'], ['event_registration.tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('registration_id', 'registration_tag_id'),
        schema='event_registration'
    )


def downgrade():
    op.drop_table('registration_tags', schema='event_registration')
    op.drop_table('tags', schema='event_registration')
