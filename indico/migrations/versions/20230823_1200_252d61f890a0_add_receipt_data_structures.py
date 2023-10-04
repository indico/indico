"""Add receipt data structures

Revision ID: 252d61f890a0
Revises: 0c44046dc1be
Create Date: 2021-10-01 15:30:14.789502
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.enum import IndicoIntEnum


# revision identifiers, used by Alembic.
revision = '252d61f890a0'
down_revision = '0c44046dc1be'
branch_labels = None
depends_on = None


class _ReceiptTemplateType(IndicoIntEnum):
    none = 0
    receipt = 1
    certificate = 2


def upgrade():
    op.create_table(
        'receipt_templates',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('type', PyIntEnum(_ReceiptTemplateType), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True, index=True),
        sa.Column('category_id', sa.Integer(), nullable=True, index=True),
        sa.Column('html', sa.String(), nullable=False),
        sa.Column('css', sa.String(), nullable=False),
        sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint('(event_id IS NULL) != (category_id IS NULL)', name='event_xor_category_id_null'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        schema='indico',
    )
    op.create_table(
        'receipt_files',
        sa.Column('file_id', sa.Integer(), nullable=False, index=True),
        sa.Column('registration_id', sa.Integer(), nullable=False, index=True),
        sa.Column('template_id', sa.Integer(), nullable=False, index=True),
        sa.Column('template_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['indico.files.id']),
        sa.ForeignKeyConstraint(['registration_id'], ['event_registration.registrations.id']),
        sa.ForeignKeyConstraint(['template_id'], ['indico.receipt_templates.id']),
        sa.PrimaryKeyConstraint('file_id'),
        schema='event_registration'
    )


def downgrade():
    op.drop_table('receipt_files', schema='event_registration')
    op.drop_table('receipt_templates', schema='indico')
