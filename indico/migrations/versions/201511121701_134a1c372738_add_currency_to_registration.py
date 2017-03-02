"""Add currency to registration

Revision ID: 134a1c372738
Revises: 98f411f40bb
Create Date: 2015-11-12 17:01:41.117908
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '134a1c372738'
down_revision = '98f411f40bb'


def upgrade():
    op.add_column('forms', sa.Column('currency', sa.String(), nullable=True), schema='event_registration')
    op.add_column('registrations', sa.Column('currency', sa.String(), nullable=True), schema='event_registration')
    op.execute("""
        UPDATE event_registration.forms f SET currency = coalesce(
            (SELECT value FROM events.settings WHERE module = 'payment' AND name = 'currency' AND event_id = f.event_id),
            (SELECT value FROM indico.settings WHERE module = 'payment' AND name = 'currency')
        ) #>> '{}'
    """)
    op.execute("DELETE FROM events.settings WHERE module = 'payment' AND name = 'currency'")
    op.execute("""
        UPDATE event_registration.registrations r SET currency = (
            SELECT currency FROM event_registration.forms WHERE id = r.registration_form_id
        )
    """)
    op.alter_column('forms', 'currency', nullable=False, schema='event_registration')
    op.alter_column('registrations', 'currency', nullable=False, schema='event_registration')


def downgrade():
    op.execute("""
        INSERT INTO events.settings (event_id, module, name, value)
            SELECT DISTINCT ON (event_id) event_id, 'payment', 'currency', to_json(currency)
            FROM event_registration.forms ORDER BY event_id
    """)
    op.drop_column('registrations', 'currency', schema='event_registration')
    op.drop_column('forms', 'currency', schema='event_registration')
