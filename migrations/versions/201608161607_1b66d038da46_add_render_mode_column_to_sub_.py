"""Add render_mode column to (sub-)contribution descriptions

Revision ID: 1b66d038da46
Revises: 8763fe20f41
Create Date: 2016-08-16 16:07:25.177573
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.descriptions import RenderMode


# revision identifiers, used by Alembic.
revision = '1b66d038da46'
down_revision = '8763fe20f41'


def upgrade():
    markdown_mode = str(RenderMode.markdown.value)
    print 'Adding render_mode column to (sub-)contributions - this may take some time!'
    op.add_column('contributions', sa.Column('render_mode', PyIntEnum(RenderMode), server_default=markdown_mode,
                                             nullable=False), schema='events')
    op.add_column('subcontributions', sa.Column('render_mode', PyIntEnum(RenderMode), server_default=markdown_mode,
                                                nullable=False), schema='events')
    op.alter_column('contributions', 'render_mode', server_default=None, schema='events')
    op.alter_column('subcontributions', 'render_mode', server_default=None, schema='events')

    # set legacy (sub-)contributions with a description to 'html'
    print 'Updating legacy (sub-)contributions - this may take some time!'
    op.execute("""
        CREATE TEMP TABLE html_contribs ON COMMIT DROP AS (
            SELECT id FROM events.contributions c
            WHERE description != '' AND
                  EXISTS (SELECT 1 FROM events.legacy_contribution_id_map WHERE contribution_id = c.id)
        );
        CREATE TEMP TABLE html_subcontribs ON COMMIT DROP AS (
            SELECT id FROM events.subcontributions sc
            WHERE description != '' AND
                  EXISTS (SELECT 1 FROM events.legacy_subcontribution_id_map WHERE subcontribution_id = sc.id)
        );
    """)
    op.execute("""
        UPDATE events.contributions c SET render_mode = {0:d} FROM html_contribs hc WHERE hc.id = c.id;
        UPDATE events.subcontributions sc SET render_mode = {0:d} FROM html_subcontribs hs WHERE hs.id = sc.id;
    """.format(RenderMode.html.value))

    # support all render modes for notes
    op.drop_constraint('ck_note_revisions_valid_enum_render_mode', 'note_revisions', schema='events')
    op.create_check_constraint('valid_enum_render_mode', 'note_revisions', 'render_mode IN (1, 2, 3)', schema='events')


def downgrade():
    op.drop_constraint('ck_note_revisions_valid_enum_render_mode', 'note_revisions', schema='events')
    op.create_check_constraint('valid_enum_render_mode', 'note_revisions', 'render_mode IN (1, 2)', schema='events')
    op.drop_column('subcontributions', 'render_mode', schema='events')
    op.drop_column('contributions', 'render_mode', schema='events')
