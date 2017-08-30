"""Fix page_size setting capitalization

Revision ID: 65c079b091bf
Revises: 09fd62e56097
Create Date: 2017-08-30 15:35:54.187063
"""

import sqlalchemy as sa
from alembic import context, op

from indico.modules.events.models.settings import EventSetting


# revision identifiers, used by Alembic.
revision = '65c079b091bf'
down_revision = '09fd62e56097'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    table = EventSetting.__table__
    op.execute(table.update()
               .where(sa.and_(table.c.module == 'badge',
                              table.c.name == 'page_size',
                              table.c.value.op('#>>')('{}') == 'Letter'))
               .values(value='letter'))


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    table = EventSetting.__table__
    op.execute(table.update()
               .where(sa.and_(table.c.module == 'badge',
                              table.c.name == 'page_size',
                              table.c.value.op('#>>')('{}') == 'letter'))
               .values(value='Letter'))
