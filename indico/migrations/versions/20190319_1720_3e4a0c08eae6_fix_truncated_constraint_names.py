"""Fix truncated constraint names (sqlalchemy 1.3)

Revision ID: 3e4a0c08eae6
Revises: 081d4c97060a
Create Date: 2019-03-19 17:20:54.724305
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3e4a0c08eae6'
down_revision = '081d4c97060a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        ALTER TABLE event_abstracts.abstract_review_ratings
        DROP CONSTRAINT fk_abstract_review_ratings_question_id_abstract_review_question;

        ALTER TABLE event_abstracts.abstract_review_ratings
        ADD CONSTRAINT fk_abstract_review_ratings_question_id_abstract_review__aa27
        FOREIGN KEY (question_id) REFERENCES event_abstracts.abstract_review_questions(id);

        ALTER TABLE event_abstracts.abstract_reviews
        DROP CONSTRAINT fk_abstract_reviews_proposed_contribution_type_id_contribution_;

        ALTER TABLE event_abstracts.abstract_reviews
        ADD CONSTRAINT fk_abstract_reviews_proposed_contribution_type_id_contr_6290
        FOREIGN KEY (proposed_contribution_type_id) REFERENCES events.contribution_types(id);


        ALTER TABLE events.subcontribution_person_links
        DROP CONSTRAINT fk_subcontribution_person_links_subcontribution_id_subcontribut;

        ALTER TABLE events.subcontribution_person_links
        ADD CONSTRAINT fk_subcontribution_person_links_subcontribution_id_subc_0455
        FOREIGN KEY (subcontribution_id) REFERENCES events.subcontributions(id);

        ALTER TABLE events.subcontribution_references
        DROP CONSTRAINT fk_subcontribution_references_subcontribution_id_subcontributio;

        ALTER TABLE events.subcontribution_references
        ADD CONSTRAINT fk_subcontribution_references_subcontribution_id_subcon_bb79
        FOREIGN KEY (subcontribution_id)  REFERENCES events.subcontributions(id);
    ''')


def downgrade():
    op.execute('''
        ALTER TABLE event_abstracts.abstract_review_ratings
        DROP CONSTRAINT fk_abstract_review_ratings_question_id_abstract_review__aa27;

        ALTER TABLE event_abstracts.abstract_review_ratings
        ADD CONSTRAINT fk_abstract_review_ratings_question_id_abstract_review_question
        FOREIGN KEY (question_id) REFERENCES event_abstracts.abstract_review_questions(id);

        ALTER TABLE event_abstracts.abstract_reviews
        DROP CONSTRAINT fk_abstract_reviews_proposed_contribution_type_id_contr_6290;

        ALTER TABLE event_abstracts.abstract_reviews
        ADD CONSTRAINT fk_abstract_reviews_proposed_contribution_type_id_contribution_
        FOREIGN KEY (proposed_contribution_type_id) REFERENCES events.contribution_types(id);


        ALTER TABLE events.subcontribution_person_links
        DROP CONSTRAINT fk_subcontribution_person_links_subcontribution_id_subc_0455;

        ALTER TABLE events.subcontribution_person_links
        ADD CONSTRAINT fk_subcontribution_person_links_subcontribution_id_subcontribut
        FOREIGN KEY (subcontribution_id) REFERENCES events.subcontributions(id);

        ALTER TABLE events.subcontribution_references
        DROP CONSTRAINT fk_subcontribution_references_subcontribution_id_subcon_bb79;

        ALTER TABLE events.subcontribution_references
        ADD CONSTRAINT fk_subcontribution_references_subcontribution_id_subcontributio
        FOREIGN KEY (subcontribution_id)  REFERENCES events.subcontributions(id);
    ''')
