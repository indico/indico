"""Delete obsolete user links

Revision ID: 2f57a1a87b83
Revises: 172df07a4f62
Create Date: 2016-11-16 13:44:42.984178
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '2f57a1a87b83'
down_revision = '172df07a4f62'


def upgrade():
    op.execute("""
        DELETE FROM users.links
        WHERE type != 'conference' OR role NOT IN (
            'editor', 'paperReviewManager', 'referee', 'reviewer'
        )
    """)


def downgrade():
    pass
