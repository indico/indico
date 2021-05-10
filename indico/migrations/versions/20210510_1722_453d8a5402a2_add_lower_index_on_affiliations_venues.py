"""Add lower index on affiliations+venues

Revision ID: 453d8a5402a2
Revises: d89585afaf2e
Create Date: 2021-05-10 17:22:06.565069
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '453d8a5402a2'
down_revision = 'd89585afaf2e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        CREATE INDEX ix_uq_affiliations_name_lower ON users.affiliations USING btree (lower(name));
        CREATE INDEX ix_uq_breaks_venue_name_lower ON events.breaks USING btree (lower(venue_name));
        CREATE INDEX ix_uq_contributions_venue_name_lower ON events.contributions USING btree (lower(venue_name));
        CREATE INDEX ix_uq_events_venue_name_lower ON events.events USING btree (lower(venue_name));
        CREATE INDEX ix_uq_locations_name_lower ON roombooking.locations USING btree (lower(name));
        CREATE INDEX ix_uq_session_blocks_venue_name_lower ON events.session_blocks USING btree (lower(venue_name));
        CREATE INDEX ix_uq_sessions_venue_name_lower ON events.sessions USING btree (lower(venue_name));
    ''')


def downgrade():
    op.execute('''
        DROP INDEX events.ix_uq_breaks_venue_name_lower;
        DROP INDEX events.ix_uq_contributions_venue_name_lower;
        DROP INDEX events.ix_uq_events_venue_name_lower;
        DROP INDEX events.ix_uq_session_blocks_venue_name_lower;
        DROP INDEX events.ix_uq_sessions_venue_name_lower;
        DROP INDEX roombooking.ix_uq_locations_name_lower;
        DROP INDEX users.ix_uq_affiliations_name_lower;
    ''')
