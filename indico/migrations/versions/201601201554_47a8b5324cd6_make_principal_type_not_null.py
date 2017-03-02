"""Make principal type NOT NULL

Revision ID: 47a8b5324cd6
Revises: 43f6a1414c75
Create Date: 2016-01-20 15:54:59.244972
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '47a8b5324cd6'
down_revision = '43f6a1414c75'


def upgrade():
    op.alter_column('attachment_principals', 'type', nullable=False, schema='attachments')
    op.alter_column('folder_principals', 'type', nullable=False, schema='attachments')
    op.alter_column('contribution_principals', 'type', nullable=False, schema='events')
    op.alter_column('principals', 'type', nullable=False, schema='events')
    op.alter_column('session_principals', 'type', nullable=False, schema='events')
    op.alter_column('settings_principals', 'type', nullable=False, schema='events')
    op.alter_column('settings_principals', 'type', nullable=False, schema='indico')
    op.alter_column('blocking_principals', 'type', nullable=False, schema='roombooking')


def downgrade():
    op.alter_column('attachment_principals', 'type', nullable=True, schema='attachments')
    op.alter_column('folder_principals', 'type', nullable=True, schema='attachments')
    op.alter_column('contribution_principals', 'type', nullable=True, schema='events')
    op.alter_column('principals', 'type', nullable=True, schema='events')
    op.alter_column('session_principals', 'type', nullable=True, schema='events')
    op.alter_column('settings_principals', 'type', nullable=True, schema='events')
    op.alter_column('settings_principals', 'type', nullable=True, schema='indico')
    op.alter_column('blocking_principals', 'type', nullable=True, schema='roombooking')
