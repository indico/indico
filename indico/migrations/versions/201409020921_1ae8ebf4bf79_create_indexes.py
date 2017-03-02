"""Create indexes

Revision ID: 1ae8ebf4bf79
Revises: None
Create Date: 2014-09-02 09:21:41.743542
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import TSVECTOR


# revision identifiers, used by Alembic.
revision = '1ae8ebf4bf79'
down_revision = None


def upgrade():
    op.execute('CREATE SCHEMA events')
    op.create_table('event_index',
                    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('title_vector', TSVECTOR(), autoincrement=False, nullable=True),
                    sa.Column('start_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
                    sa.PrimaryKeyConstraint('id', name=u'event_index_pkey'),
                    sa.Index('title_vector_idx', 'title_vector', postgresql_using='gin'),
                    schema='events')

    op.create_table('category_index',
                    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('title_vector', TSVECTOR(), autoincrement=False, nullable=True),
                    sa.PrimaryKeyConstraint('id', name=u'category_index_pkey'),
                    sa.Index('title_vector_idx', 'title_vector', postgresql_using='gin'),
                    schema='indico')


def downgrade():
    op.drop_table('event_index', schema='events')
    op.execute('DROP SCHEMA events')

    op.drop_table('category_index', schema='indico')
