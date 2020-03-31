"""Associate review-conditions with editable types

Revision ID: 3c5462aef0b7
Revises: 6444c893a21f
Create Date: 2020-03-31 12:51:40.822239
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3c5462aef0b7'
down_revision = '6444c893a21f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE events.settings
        SET name = 'paper_review_conditions'
        WHERE module = 'editing' AND name = 'review_conditions'
    """)


def downgrade():
    op.execute("""
        UPDATE events.settings
        SET name = 'review_conditions'
        WHERE module = 'editing' AND name = 'paper_review_conditions'
    """)
    op.execute("""
        DELETE FROM events.settings
        WHERE module = 'editing' AND name IN ('slides_review_conditions', 'poster_review_conditions')
    """)
