#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

import click
import yaml

from indico.web.flask.app import make_app


def _main(name, template_id, target):
    from indico.modules.receipts.models.templates import ReceiptTemplate
    from indico.modules.receipts.schemas import ReceiptTemplateDBSchema
    template = ReceiptTemplate.get(template_id)
    data = ReceiptTemplateDBSchema(only=('title', 'default_filename')).dump(template)

    metadata_file = target / f'{name}.yaml'
    if metadata_file.exists():
        existing_data = yaml.safe_load(metadata_file.read_text())
        data['version'] = existing_data.get('version', 0) + 1
    else:
        data['version'] = 1
    template_path = target / name
    template_path.mkdir(parents=True, exist_ok=True)

    metadata_file.write_text(yaml.dump(data))
    (template_path / 'template.html').write_text(template.html)
    (template_path / 'theme.css').write_text(template.css)
    (template_path / 'metadata.yaml').write_text(template.yaml)


@click.command()
@click.argument('name')
@click.argument('template_id', type=int)
@click.option('-t', '--target', type=click.Path(), default='indico/modules/receipts/default_templates',
              help='Output directory for the template files')
def main(name, template_id, target):
    with make_app().app_context():
        _main(name, template_id, Path(target))


if __name__ == '__main__':
    main()
