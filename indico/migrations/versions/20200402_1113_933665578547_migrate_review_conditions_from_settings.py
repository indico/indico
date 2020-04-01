"""Migrate review conditions from settings

Revision ID: 933665578547
Revises: 02bf20df06b3
Create Date: 2020-04-02 11:13:58.931020
"""

import json
from collections import defaultdict
from uuid import uuid4

from alembic import context, op

from indico.modules.events.editing.models.editable import EditableType


# revision identifiers, used by Alembic.
revision = '933665578547'
down_revision = '02bf20df06b3'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    for type_ in EditableType:
        res = conn.execute(
            "SELECT event_id, value FROM events.settings WHERE module = 'editing' AND name = %s",
            ("{}_review_conditions".format(type_.name),),
        )
        for event_id, value in res:
            for condition in value:
                res2 = conn.execute(
                    "INSERT INTO event_editing.review_conditions (type, event_id) VALUES (%s, %s) RETURNING id",
                    (type_, event_id),
                )
                revcon_id = res2.fetchone()[0]
                for file_type in condition[1]:
                    conn.execute("""
                        INSERT INTO event_editing.review_condition_file_types (file_type_id, review_condition_id)
                        VALUES (%s, %s)
                        """, (file_type, revcon_id),
                    )
        conn.execute(
            "DELETE FROM events.settings WHERE module = 'editing' AND name = %s",
            ("{}_review_conditions".format(type_.name),),
        )


def downgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    for type_ in EditableType:
        res = conn.execute("SELECT id, event_id FROM event_editing.review_conditions WHERE type = %s", (type_.value,))
        review_conditions = defaultdict(list)
        for id, event_id in res:
            file_types = conn.execute(
                "SELECT file_type_id FROM event_editing.review_condition_file_types WHERE review_condition_id = %s",
                (id,),
            )
            value = [unicode(uuid4()), [f[0] for f in file_types.fetchall()]]
            review_conditions[event_id].append(value)
        for key, value in review_conditions.items():
            conn.execute(
                "INSERT INTO events.settings (event_id, module, name, value) VALUES (%s, 'editing', %s, %s)",
                (key, "{}_review_conditions".format(type_.name), json.dumps(value)),
            )

    conn.execute("DELETE FROM event_editing.review_condition_file_types")
    conn.execute("DELETE FROM event_editing.review_conditions")
