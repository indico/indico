"""Remove Flower oauth app

Revision ID: 26806768cd3f
Revises: ecc7088914e7
Create Date: 2021-02-24 18:08:05.634719
"""

from uuid import uuid4

from alembic import op


# revision identifiers, used by Alembic.
revision = '26806768cd3f'
down_revision = 'ecc7088914e7'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('DELETE FROM oauth.applications WHERE system_app_type = 2')
    op.drop_constraint('ck_applications_valid_enum_system_app_type', 'applications', schema='oauth')
    op.create_check_constraint('valid_enum_system_app_type', 'applications', '(system_app_type = ANY (ARRAY[0, 1]))',
                               schema='oauth')


def downgrade():
    op.drop_constraint('ck_applications_valid_enum_system_app_type', 'applications', schema='oauth')
    op.create_check_constraint('valid_enum_system_app_type', 'applications', '(system_app_type = ANY (ARRAY[0, 1, 2]))',
                               schema='oauth')
    op.execute(f'''
        INSERT INTO oauth.applications
        (name, description, client_id, client_secret, allowed_scopes, redirect_uris, is_enabled, is_trusted,
         system_app_type, allow_pkce_flow)
        VALUES
        ('Flower', '', '{uuid4()}', '{uuid4()}', '{{read:user}}', '{{}}', true, true, 2, false);
    ''')
