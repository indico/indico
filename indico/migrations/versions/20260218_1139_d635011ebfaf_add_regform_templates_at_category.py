"""Add regform templates at category

Revision ID: d635011ebfaf
Revises: af9d03d7073c
Create Date: 2025-10-14 11:39:36.099229
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd635011ebfaf'
down_revision = 'af9d03d7073c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('category_id', sa.Integer(), nullable=True), schema='event_registration')
    op.add_column('forms', sa.Column('template_id', sa.Integer(), nullable=True), schema='event_registration')
    op.create_foreign_key(None, 'forms', 'categories', ['category_id'], ['id'],
                          source_schema='event_registration', referent_schema='categories')
    op.create_check_constraint('event_xor_category_id_null', 'forms', '(event_id IS NULL) != (category_id IS NULL)',
                               schema='event_registration')
    op.alter_column('forms', 'event_id', existing_type=sa.Integer(), nullable=True, schema='event_registration')
    op.execute('''
        CREATE OR REPLACE FUNCTION disallow_registration_on_forms_linked_to_categories()
        RETURNS trigger AS $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM event_registration.forms rf
                WHERE rf.id = NEW.registration_form_id
                AND rf.category_id IS NOT NULL
            ) THEN
                RAISE EXCEPTION 'Registrations cannot be linked to template forms associated with a category';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER registrations_prevent_forms_linked_to_categories
        BEFORE INSERT OR UPDATE ON event_registration.registrations
        FOR EACH ROW
        EXECUTE FUNCTION disallow_registration_on_forms_linked_to_categories();
    ''')
    op.drop_constraint('ck_logs_valid_enum_realm', 'logs', schema='categories')
    op.create_check_constraint('valid_enum_realm', 'logs', '(realm = ANY (ARRAY[1, 2, 3]))', schema='categories')


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
                sa.text('UPDATE event_registration.form_items SET current_data_id = NULL WHERE id = ANY(:form_item_ids)'),
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
    op.execute('DROP TRIGGER IF EXISTS registrations_prevent_forms_linked_to_categories ON event_registration.registrations;')
    op.execute('DROP FUNCTION IF EXISTS disallow_registration_on_forms_linked_to_categories;')
    op.execute('''DELETE FROM event_registration.forms WHERE category_id IS NOT NULL; ''')
    op.drop_constraint('ck_forms_event_xor_category_id_null', 'forms', schema='event_registration')
    op.drop_column('forms', 'category_id', schema='event_registration')
    op.drop_column('forms', 'template_id', schema='event_registration')
    op.alter_column('forms', 'event_id', existing_type=sa.Integer(), nullable=False, schema='event_registration')
    op.execute('''DELETE FROM categories.logs WHERE realm = 3;''')
    op.drop_constraint('ck_logs_valid_enum_realm', 'logs', schema='categories')
    op.create_check_constraint('valid_enum_realm', 'logs', '(realm = ANY (ARRAY[1, 2]))', schema='categories')
