"""Rename report_links table

Revision ID: 28b674f8290d
Revises: 23ef6a49ae28
Create Date: 2016-08-11 11:32:44.262861
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '28b674f8290d'
down_revision = '23ef6a49ae28'


def upgrade():
    op.rename_table('report_links', 'static_list_links', schema='events')
    op.execute('''
        ALTER INDEX events.ix_report_links_event_id RENAME TO ix_static_list_links_event_id;
        ALTER INDEX events.ix_uq_report_links_uuid RENAME TO ix_uq_static_list_links_uuid;
        ALTER SEQUENCE events.report_links_id_seq RENAME TO static_list_links_id_seq;
        ALTER TABLE events.static_list_links RENAME CONSTRAINT pk_report_links TO pk_static_list_links;
        ALTER TABLE events.static_list_links RENAME CONSTRAINT
            fk_report_links_event_id_events TO fk_static_list_links_event_id_events;
    ''')


def downgrade():
    op.rename_table('static_list_links', 'report_links', schema='events')
    op.execute('''
        ALTER INDEX events.ix_static_list_links_event_id RENAME TO ix_report_links_event_id;
        ALTER INDEX events.ix_uq_static_list_links_uuid RENAME TO ix_uq_report_links_uuid;
        ALTER SEQUENCE events.static_list_links_id_seq RENAME TO report_links_id_seq;
        ALTER TABLE events.report_links RENAME CONSTRAINT pk_static_list_links TO pk_report_links;
        ALTER TABLE events.report_links RENAME CONSTRAINT
            fk_static_list_links_event_id_events TO fk_report_links_event_id_events;
    ''')
