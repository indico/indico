"""Add regform templates at category

Revision ID: 110c2b801805
Revises: 06a037da1ec6
Create Date: 2026-08-17 16:25:49.658315
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '110c2b801805'
down_revision = '06a037da1ec6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('category_id', sa.Integer(), nullable=True), schema='event_registration')
    op.add_column('forms', sa.Column('template_id', sa.Integer(), nullable=True), schema='event_registration')
    op.create_index(None, 'forms', ['category_id'], schema='event_registration')
    op.create_index(None, 'forms', ['template_id'], schema='event_registration')
    op.create_foreign_key(None, 'forms', 'categories', ['category_id'], ['id'],
                          source_schema='event_registration', referent_schema='categories')
    op.create_foreign_key(None, 'forms', 'forms', ['template_id'], ['id'], source_schema='event_registration',
                          referent_schema='event_registration', ondelete='SET NULL')
    op.create_check_constraint('event_xor_category_id_null', 'forms', '(event_id IS NULL) != (category_id IS NULL)',
                               schema='event_registration')
    op.create_check_constraint('not_created_from_self', 'forms', 'template_id != id', schema='event_registration')
    op.alter_column('forms', 'event_id', type_=sa.Integer(), nullable=True, schema='event_registration')


def downgrade():
    conn = op.get_bind()
    form_ids = [form for form, in conn.execute(
        sa.text('SELECT id FROM event_registration.forms WHERE category_id IS NOT NULL')
    )]
    if form_ids:
        form_item_ids = [item for item, in conn.execute(
            sa.text('SELECT id FROM event_registration.form_items WHERE registration_form_id = ANY(:form_ids)'),
            {'form_ids': form_ids}
        )]
        if form_item_ids:
            conn.execute(
                sa.text('UPDATE event_registration.form_items SET current_data_id = NULL '
                        'WHERE id = ANY(:form_item_ids)'),
                {'form_item_ids': form_item_ids}
            )
            conn.execute(
                sa.text('DELETE FROM event_registration.form_field_data WHERE field_id = ANY(:item_ids)'),
                {'item_ids': form_item_ids}
            )
            conn.execute(
                sa.text('DELETE FROM event_registration.form_items WHERE id = ANY(:item_ids)'),
                {'item_ids': form_item_ids}
            )
        conn.execute(
            sa.text('DELETE FROM event_registration.forms WHERE id = ANY(:form_ids)'),
            {'form_ids': form_ids}
        )
    op.drop_constraint('ck_forms_not_created_from_self', 'forms', schema='event_registration')
    op.drop_constraint('ck_forms_event_xor_category_id_null', 'forms', schema='event_registration')
    op.drop_column('forms', 'template_id', schema='event_registration')
    op.drop_column('forms', 'category_id', schema='event_registration')
    op.alter_column('forms', 'event_id', type_=sa.Integer(), nullable=False, schema='event_registration')
