"""Make agreement email nullable

Revision ID: 49ac5164a65b
Revises: 233928da84b2
Create Date: 2015-03-05 10:56:05.053603
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '49ac5164a65b'
down_revision = '233928da84b2'


def upgrade():
    op.alter_column('agreements', 'person_email', nullable=True, schema='events')


def downgrade():
    op.alter_column('agreements', 'person_email', nullable=False, schema='events')
