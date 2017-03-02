"""Update paper menu entries

Revision ID: 431e3a9178ab
Revises: 4dd759c93728
Create Date: 2017-02-07 17:40:18.857168
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '431e3a9178ab'
down_revision = '4dd759c93728'


def upgrade():
    # Get rid of all the obsolete legacy paper-related menu entries
    op.execute("""
        DELETE FROM events.menu_entries
        WHERE type = 2 AND name IN (
            'paper_setup', 'paper_assign', 'contributions_to_judge', 'contributions_as_reviewer',
            'contributions_as_editor', 'paper_upload', 'download_template'
        )
    """)
    # People might have renamed the parent menu item so we keep that one
    op.execute("""
        UPDATE events.menu_entries SET name = 'call_for_papers'
        WHERE type = 2 AND name = 'paper_reviewing'
    """)


def downgrade():
    pass
