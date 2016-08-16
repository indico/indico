import os

from flask.json import htmlsafe_dumps
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import load_only

# Used only by imports in the next block
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.contributions.models.references import SubContributionReference
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.modules.rb.models.holidays import Holiday

from indico.web.flask.app import make_app

from indico.core.db import DBMgr, db
from indico.core.db.sqlalchemy.util.session import update_session_options
from indico.modules.categories.models.categories import Category
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution


def main():
    html_tag_regex = '<[a-zA-Z]+.*>'
    contributions = (Contribution.query
                     .filter(Contribution.description.op('~')(html_tag_regex))
                     .options(load_only('id', 'description'))
                     .all())
    subcontributions = (SubContribution.query
                        .filter(SubContribution.description.op('~')(html_tag_regex))
                        .options(load_only('id', 'description'))
                        .all())
    categories = (Category.query
                  .filter(Category.description.op('~')(html_tag_regex))
                  .options(load_only('id', 'description'))
                  .all())

    def as_dict(objs):
        return {x.id: x.description for x in objs}

    def format_table(model):
        return model.__table__.fullname

    object_descriptions = {
        format_table(Contribution): as_dict(contributions),
        format_table(SubContribution): as_dict(subcontributions),
        format_table(Category): as_dict(categories)
    }

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))

    template = env.get_template('fix_descriptions_template.html')
    print template.render(object_descriptions=htmlsafe_dumps(object_descriptions))


if __name__ == '__main__':
    update_session_options(db)
    with make_app().app_context():
        with DBMgr.getInstance().global_connection():
            main()
