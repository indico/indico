"""Switch from JSON to JSONB

Revision ID: 06a4ec717b84
Revises: 7024f7f66e20
Create Date: 2019-05-17 13:13:31.784858
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '06a4ec717b84'
down_revision = '7024f7f66e20'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        ALTER TABLE categories.categories
            ALTER COLUMN icon_metadata TYPE jsonb,
            ALTER COLUMN logo_metadata TYPE jsonb,
            ALTER COLUMN default_event_themes TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE categories.settings
            ALTER COLUMN "value" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.abstract_field_values
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.abstract_review_questions
            ALTER COLUMN field_data TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.abstract_review_ratings
            ALTER COLUMN "value" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.email_logs
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.email_templates
            ALTER COLUMN rules TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_paper_reviewing.review_questions
            ALTER COLUMN field_data TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_paper_reviewing.review_ratings
            ALTER COLUMN "value" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_registration.form_field_data
            ALTER COLUMN versioned_data TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_registration.form_items
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_surveys.answers
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_surveys.items
            ALTER COLUMN field_data TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE event_surveys.submissions
            ALTER COLUMN pending_answers TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE events.agreements
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE events.contribution_field_values
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE events.contribution_fields
            ALTER COLUMN field_data TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE events.events
            ALTER COLUMN logo_metadata TYPE jsonb,
            ALTER COLUMN stylesheet_metadata TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE events.payment_transactions
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE events.requests
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE events.settings
            ALTER COLUMN "value" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE indico.designer_templates
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE indico.settings
            ALTER COLUMN "value" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE roombooking.room_attribute_values
            ALTER COLUMN "value" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE users.identities
            ALTER COLUMN multipass_data TYPE jsonb,
            ALTER COLUMN "data" TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE users.registration_requests
            ALTER COLUMN user_data TYPE jsonb,
            ALTER COLUMN identity_data TYPE jsonb,
            ALTER COLUMN settings TYPE jsonb;
    ''')
    op.execute('''
        ALTER TABLE users.settings
            ALTER COLUMN "value" TYPE jsonb;
    ''')


def downgrade():
    op.execute('''
        ALTER TABLE categories.categories
            ALTER COLUMN icon_metadata TYPE json,
            ALTER COLUMN logo_metadata TYPE json,
            ALTER COLUMN default_event_themes TYPE json;
    ''')
    op.execute('''
        ALTER TABLE categories.settings
            ALTER COLUMN "value" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.abstract_field_values
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.abstract_review_questions
            ALTER COLUMN field_data TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.abstract_review_ratings
            ALTER COLUMN "value" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.email_logs
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_abstracts.email_templates
            ALTER COLUMN rules TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_paper_reviewing.review_questions
            ALTER COLUMN field_data TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_paper_reviewing.review_ratings
            ALTER COLUMN "value" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_registration.form_field_data
            ALTER COLUMN versioned_data TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_registration.form_items
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_surveys.answers
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_surveys.items
            ALTER COLUMN field_data TYPE json;
    ''')
    op.execute('''
        ALTER TABLE event_surveys.submissions
            ALTER COLUMN pending_answers TYPE json;
    ''')
    op.execute('''
        ALTER TABLE events.agreements
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE events.contribution_field_values
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE events.contribution_fields
            ALTER COLUMN field_data TYPE json;
    ''')
    op.execute('''
        ALTER TABLE events.events
            ALTER COLUMN logo_metadata TYPE json,
            ALTER COLUMN stylesheet_metadata TYPE json;
    ''')
    op.execute('''
        ALTER TABLE events.payment_transactions
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE events.requests
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE events.settings
            ALTER COLUMN "value" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE indico.designer_templates
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE indico.settings
            ALTER COLUMN "value" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE roombooking.room_attribute_values
            ALTER COLUMN "value" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE users.identities
            ALTER COLUMN multipass_data TYPE json,
            ALTER COLUMN "data" TYPE json;
    ''')
    op.execute('''
        ALTER TABLE users.registration_requests
            ALTER COLUMN user_data TYPE json,
            ALTER COLUMN identity_data TYPE json,
            ALTER COLUMN settings TYPE json;
    ''')
    op.execute('''
        ALTER TABLE users.settings
            ALTER COLUMN "value" TYPE json;
    ''')
