"""Add a redirect URI for the new Check-in app

Revision ID: fb0ca1440185
Revises: 252d61f890a0
Create Date: 2023-11-24 09:41:25.897835
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'fb0ca1440185'
down_revision = '252d61f890a0'
branch_labels = None
depends_on = None

checkin_app_type = 1
redirect_uri = 'https://checkin.getindico.io'


def upgrade():
    op.execute(f'''
        UPDATE oauth.applications
        SET redirect_uris = array_append(redirect_uris, '{redirect_uri}')
        WHERE system_app_type = {checkin_app_type}
    ''')  # noqa: S608


def downgrade():
    op.execute(f'''
        UPDATE oauth.applications
        SET redirect_uris = array_remove(redirect_uris, '{redirect_uri}')
        WHERE system_app_type = {checkin_app_type}
    ''')  # noqa: S608
