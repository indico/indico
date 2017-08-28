"""Add default ticket template

Revision ID: bf8a98f310b3
Revises: aecc0b2792bb
Create Date: 2017-08-18 11:12:35.662385
"""

import json

from alembic import context, op

from indico.core.db.sqlalchemy.util.management import DEFAULT_TEMPLATE_DATA
from indico.modules.designer import TemplateType


# revision identifiers, used by Alembic.
revision = 'bf8a98f310b3'
down_revision = 'aecc0b2792bb'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')

    conn = op.get_bind()
    query = '''
        INSERT INTO indico.designer_templates
            (category_id, title, type, data, is_system_template, is_clonable)
        VALUES
            (0, 'Default ticket', %s, %s, true, true)
        RETURNING id
    '''
    res = conn.execute(query, (TemplateType.badge.value, json.dumps(DEFAULT_TEMPLATE_DATA)))
    template_id = res.fetchone()[0]
    conn.execute('UPDATE categories.categories SET default_ticket_template_id = %s WHERE id = 0',
                 (template_id,))


def downgrade():
    pass
