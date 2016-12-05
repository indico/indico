"""Rename legacy paper tables

Revision ID: 1e94b3cf3cfd
Revises: 57732e1f7e20
Create Date: 2016-12-05 17:17:16.263271
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '1e94b3cf3cfd'
down_revision = '57732e1f7e20'


def upgrade():
    op.rename_table('paper_files', 'legacy_paper_files', schema='event_paper_reviewing')
    op.rename_table('contribution_roles', 'legacy_contribution_roles', schema='event_paper_reviewing')
    op.execute('''
        ALTER SEQUENCE event_paper_reviewing.paper_files_id_seq RENAME TO legacy_paper_files_id_seq;
        ALTER INDEX event_paper_reviewing.ix_paper_files_contribution_id
            RENAME TO ix_legacy_paper_files_contribution_id;
        ALTER TABLE event_paper_reviewing.legacy_paper_files
            RENAME CONSTRAINT pk_paper_files
            TO pk_legacy_paper_files;
        ALTER TABLE event_paper_reviewing.legacy_paper_files
            RENAME CONSTRAINT fk_paper_files_contribution_id_contributions
            TO fk_legacy_paper_files_contribution_id_contributions;

        ALTER SEQUENCE event_paper_reviewing.contribution_roles_id_seq RENAME TO legacy_contribution_roles_id_seq;
        ALTER INDEX event_paper_reviewing.ix_contribution_roles_contribution_id
            RENAME TO ix_legacy_contribution_roles_contribution_id;
        ALTER INDEX event_paper_reviewing.ix_contribution_roles_role
            RENAME TO ix_legacy_contribution_roles_role;
        ALTER INDEX event_paper_reviewing.ix_contribution_roles_user_id
            RENAME TO ix_legacy_contribution_roles_user_id;
        ALTER TABLE event_paper_reviewing.legacy_contribution_roles
            RENAME CONSTRAINT pk_contribution_roles
            TO pk_legacy_contribution_roles;
        ALTER TABLE event_paper_reviewing.legacy_contribution_roles
            RENAME CONSTRAINT fk_contribution_roles_contribution_id_contributions
            TO fk_legacy_contribution_roles_contribution_id_contributions;
        ALTER TABLE event_paper_reviewing.legacy_contribution_roles
            RENAME CONSTRAINT fk_contribution_roles_user_id_users
            TO fk_legacy_contribution_roles_user_id_users;
        ALTER TABLE event_paper_reviewing.legacy_contribution_roles
            RENAME CONSTRAINT ck_contribution_roles_valid_enum_role
            TO ck_legacy_contribution_roles_valid_enum_role;
    ''')


def downgrade():
    op.rename_table('legacy_paper_files', 'paper_files', schema='event_paper_reviewing')
    op.rename_table('legacy_contribution_roles', 'contribution_roles', schema='event_paper_reviewing')
    op.execute('''
        ALTER SEQUENCE event_paper_reviewing.legacy_contribution_roles_id_seq RENAME TO contribution_roles_id_seq;
        ALTER INDEX event_paper_reviewing.ix_legacy_contribution_roles_contribution_id
            RENAME TO ix_contribution_roles_contribution_id;
        ALTER INDEX event_paper_reviewing.ix_legacy_contribution_roles_role
            RENAME TO ix_contribution_roles_role;
        ALTER INDEX event_paper_reviewing.ix_legacy_contribution_roles_user_id
            RENAME TO ix_contribution_roles_user_id;
        ALTER TABLE event_paper_reviewing.contribution_roles
            RENAME CONSTRAINT pk_legacy_contribution_roles
            TO pk_contribution_roles;
        ALTER TABLE event_paper_reviewing.contribution_roles
            RENAME CONSTRAINT fk_legacy_contribution_roles_contribution_id_contributions
            TO fk_contribution_roles_contribution_id_contributions;
        ALTER TABLE event_paper_reviewing.contribution_roles
            RENAME CONSTRAINT fk_legacy_contribution_roles_user_id_users
            TO fk_contribution_roles_user_id_users;
        ALTER TABLE event_paper_reviewing.contribution_roles
            RENAME CONSTRAINT ck_legacy_contribution_roles_valid_enum_role
            TO ck_contribution_roles_valid_enum_role;

        ALTER SEQUENCE event_paper_reviewing.legacy_paper_files_id_seq RENAME TO paper_files_id_seq;
        ALTER INDEX event_paper_reviewing.ix_legacy_paper_files_contribution_id
            RENAME TO ix_paper_files_contribution_id;
        ALTER TABLE event_paper_reviewing.paper_files
            RENAME CONSTRAINT pk_legacy_paper_files
            TO pk_paper_files;
        ALTER TABLE event_paper_reviewing.paper_files
            RENAME CONSTRAINT fk_legacy_paper_files_contribution_id_contributions
            TO fk_paper_files_contribution_id_contributions;
    ''')
