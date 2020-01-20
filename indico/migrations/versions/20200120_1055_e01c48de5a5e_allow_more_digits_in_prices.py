"""Allow more digits in prices

Revision ID: e01c48de5a5e
Revises: 2496c4adc7e9
Create Date: 2020-01-20 10:55:03.139046
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'e01c48de5a5e'
down_revision = '2496c4adc7e9'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        ALTER TABLE event_registration.forms
            ALTER COLUMN base_price SET DATA TYPE numeric(11,2) USING base_price::numeric(11,2);
        ALTER TABLE event_registration.registrations
            ALTER COLUMN base_price SET DATA TYPE numeric(11,2) USING base_price::numeric(11,2);
        ALTER TABLE event_registration.registrations
            ALTER COLUMN price_adjustment SET DATA TYPE numeric(11,2) USING price_adjustment::numeric(11,2);
        ALTER TABLE events.payment_transactions
            ALTER COLUMN amount SET DATA TYPE numeric(11,2) USING amount::numeric(11,2);
    ''')


def downgrade():
    op.execute('''
        ALTER TABLE event_registration.forms
            ALTER COLUMN base_price SET DATA TYPE numeric(8,2) USING base_price::numeric(8,2);
        ALTER TABLE event_registration.registrations
            ALTER COLUMN base_price SET DATA TYPE numeric(8,2) USING base_price::numeric(8,2);
        ALTER TABLE event_registration.registrations
            ALTER COLUMN price_adjustment SET DATA TYPE numeric(8,2) USING price_adjustment::numeric(8,2);
        ALTER TABLE events.payment_transactions
            ALTER COLUMN amount SET DATA TYPE numeric(8,2) USING amount::numeric(8,2);
    ''')
