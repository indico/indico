# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import print_function

import os

from flask.json import htmlsafe_dumps
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import load_only

from indico.modules.categories.models.categories import Category
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.web.flask.app import make_app


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
    print(template.render(object_descriptions=htmlsafe_dumps(object_descriptions)))


if __name__ == '__main__':
    with make_app().app_context():
        main()
