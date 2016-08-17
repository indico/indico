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
    html_mode = str(RenderMode.html.value)
    op.add_column('contributions',
                  sa.Column('render_mode', PyIntEnum(RenderMode), server_default=html_mode, nullable=False),
                  schema='events')
    op.add_column('subcontributions',
                  sa.Column('render_mode', PyIntEnum(RenderMode), server_default=html_mode, nullable=False),
                  schema='events')

    # set 'non-legacy' (sub-)contributions to 'markdown'
    op.execute("""CREATE TEMP TABLE markdown_contribs
                  ON COMMIT DROP
                  AS (SELECT id FROM events.contributions c
                      WHERE NOT EXISTS (SELECT 1 FROM events.legacy_contribution_id_map
                                        WHERE contribution_id = c.id))""")
    op.execute("UPDATE events.contributions c SET render_mode = %d FROM markdown_contribs mc WHERE mc.id = c.id;" %
               RenderMode.markdown)
    op.execute("""CREATE TEMP TABLE markdown_subcontribs
                  ON COMMIT DROP
                  AS (SELECT id FROM events.subcontributions c
                      WHERE NOT EXISTS (SELECT 1 FROM events.legacy_subcontribution_id_map
                                        WHERE subcontribution_id = c.id))""")
    op.execute("UPDATE events.subcontributions s SET render_mode = %d FROM markdown_subcontribs m WHERE m.id = s.id;" %
               RenderMode.markdown)

    op.alter_column('contributions', 'render_mode', server_default=None, schema='events')
    op.alter_column('subcontributions', 'render_mode', server_default=None, schema='events')


def downgrade():
    op.drop_column('subcontributions', 'render_mode', schema='events')
    op.drop_column('contributions', 'render_mode', schema='events')
