"""Add menu tables

Revision ID: bda21647f61
Revises: 365fe2261342
Create Date: 2015-08-12 12:00:09.516866
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.layout.models.menu import MenuEntryType


# revision identifiers, used by Alembic.
revision = 'bda21647f61'
down_revision = '365fe2261342'


def upgrade():
    op.create_table(
        'menu_pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('html', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'menu_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True, index=True),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('new_tab', sa.Boolean(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=True),
        sa.Column('plugin', sa.String(), nullable=True),
        sa.Column('page_id', sa.Integer(), nullable=True),
        sa.Column('type', PyIntEnum(MenuEntryType), nullable=False),
        sa.CheckConstraint('(type = 1 AND title IS NULL) OR (type != 1 AND title IS NOT NULL)', name='valid_title'),
        sa.CheckConstraint('(type = 4 AND plugin IS NOT NULL) OR (type != 4 AND plugin IS NULL)', name='valid_plugin'),
        sa.CheckConstraint('(type = 5 AND page_id IS NOT NULL) OR (type != 5 AND page_id IS NULL)',
                           name='valid_page_id'),
        sa.CheckConstraint('(type IN (1, 5) AND endpoint IS NULL) OR (type NOT IN (1, 5) AND endpoint IS NOT NULL)',
                           name='valid_endpoint'),
        sa.CheckConstraint('(type IN (2, 4) AND name IS NOT NULL) OR (type NOT IN (2, 4) and name IS NULL)',
                           name='valid_name'),
        sa.ForeignKeyConstraint(['page_id'], ['events.menu_pages.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['events.menu_entries.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'position', 'parent_id'),
        schema='events'
    )
    op.create_index(None, 'menu_entries', ['event_id', 'name'], unique=True, schema='events',
                    postgresql_where=sa.text('(type = 2 OR type = 4)'))


def downgrade():
    op.drop_constraint('fk_menu_entries_page_id_menu_pages', 'menu_entries', schema='events')
    op.drop_table('menu_entries', schema='events')
    op.drop_table('menu_pages', schema='events')
