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
        'pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('html', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'legacy_page_id_map',
        sa.Column('event_id', sa.Integer(), nullable=False, index=True, autoincrement=False),
        sa.Column('legacy_page_id', sa.Integer(), nullable=False, index=True, autoincrement=False),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['page_id'], ['events.pages.id']),
        sa.PrimaryKeyConstraint('event_id', 'legacy_page_id'),
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
        sa.Column('link_url', sa.String(), nullable=True),
        sa.Column('plugin', sa.String(), nullable=True),
        sa.Column('page_id', sa.Integer(), nullable=True),
        sa.Column('type', PyIntEnum(MenuEntryType), nullable=False),
        sa.CheckConstraint('(type = 1 AND title IS NULL) OR (type != 1 AND title IS NOT NULL)', name='valid_title'),
        sa.CheckConstraint('(type = 4 AND plugin IS NOT NULL) OR (type != 4 AND plugin IS NULL)', name='valid_plugin'),
        sa.CheckConstraint('(type = 5 AND page_id IS NOT NULL) OR (type != 5 AND page_id IS NULL)',
                           name='valid_page_id'),
        sa.CheckConstraint('(type = 3) = (link_url IS NOT NULL)',
                           name='valid_link_url'),
        sa.CheckConstraint('(type IN (2, 4) AND name IS NOT NULL) OR (type NOT IN (2, 4) and name IS NULL)',
                           name='valid_name'),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['page_id'], ['events.pages.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['events.menu_entries.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index(None, 'menu_entries', ['event_id', 'name'], unique=True, schema='events',
                    postgresql_where=sa.text('(type = 2 OR type = 4)'))
    op.add_column('events', sa.Column('default_page_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'events', ['default_page_id'], unique=False, schema='events')
    op.create_foreign_key(None,
                          'events', 'pages',
                          ['default_page_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_column('events', 'default_page_id', schema='events')
    op.drop_constraint('fk_menu_entries_page_id_pages', 'menu_entries', schema='events')
    op.drop_table('menu_entries', schema='events')
    op.drop_table('legacy_page_id_map', schema='events')
    op.drop_table('pages', schema='events')
