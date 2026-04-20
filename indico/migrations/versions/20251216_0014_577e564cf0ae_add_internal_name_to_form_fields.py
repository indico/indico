"""Add internal name to form fields

Revision ID: 577e564cf0ae
Revises: af9d03d7073c
Create Date: 2025-12-16 00:14:49.123118
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '577e564cf0ae'
down_revision = 'af9d03d7073c'
branch_labels = None
depends_on = None


class _PersonalDataType(Enum):
    email = 1
    first_name = 2
    last_name = 3
    affiliation = 4
    title = 5
    address = 6
    phone = 7
    country = 8
    position = 9
    picture = 10


def upgrade():
    op.add_column('form_items', sa.Column('internal_name', sa.String(), index=True, nullable=True),
                  schema='event_registration')
    op.create_check_constraint(
        'internal_name_not_empty',
        'form_items',
        "internal_name != ''",
        schema='event_registration'
    )
    case_expr = ' '.join(f"WHEN {e.value} THEN '{e.name.replace('_', '-')}'" for e in _PersonalDataType)
    op.execute(f'''
        UPDATE event_registration.form_items
        SET internal_name = CASE personal_data_type {case_expr} END
        WHERE personal_data_type IS NOT NULL;
    ''')  # noqa: S608
    op.create_check_constraint(
        'pd_internal_name_required',
        'form_items',
        '(internal_name IS NOT NULL) OR (personal_data_type IS NULL)',
        schema='event_registration'
    )


def downgrade():
    op.drop_column('form_items', 'internal_name', schema='event_registration')
