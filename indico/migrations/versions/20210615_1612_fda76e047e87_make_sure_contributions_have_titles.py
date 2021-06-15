"""Make sure contributions have titles

Revision ID: fda76e047e87
Revises: 735dc4e8d2f3
Create Date: 2021-06-15 16:12:55.960647
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'fda76e047e87'
down_revision = '735dc4e8d2f3'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE events.contributions SET title = '(no title)' WHERE title = '';
        UPDATE events.subcontributions SET title = '(no title)' WHERE title = '';
    ''')


def downgrade():
    pass
