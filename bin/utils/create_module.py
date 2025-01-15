# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
import textwrap
from collections import defaultdict
from datetime import date

import click


def _validate_indico_dir(ctx, param, value):
    if not os.path.isdir(value):
        raise click.BadParameter('directory does not exist')
    if not os.path.exists(os.path.join(value, 'modules')):
        raise click.BadParameter('directory has no modules subdirectory')
    return value


def _process_name(ctx, param, value):
    path = _get_module_dir(ctx.params['indico_dir'], ctx.params.get('event'), value)
    ctx.params['module_dir'] = path
    return value


def _process_model_classes(ctx, param, value):
    items = defaultdict(list)
    for item in value:
        if ':' in item:
            module_name, class_name = item.split(':', 1)
        else:
            class_name = item
            module_name = _snakify(item) + 's'
        items[module_name].append(class_name)
    return items


def _get_module_dir(indico_dir, event, name):
    segments = [indico_dir, 'modules']
    if event:
        segments.append('events')
    segments.append(name)
    return os.path.join(*segments)


def _snakify(name):
    # from http://stackoverflow.com/a/1176023/298479
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def touch(path):
    open(path, 'a').close()


def write(f, text=''):
    if text:
        f.write(text)
    f.write('\n')


def write_header(f):
    f.write(textwrap.dedent('''
        # This file is part of Indico.
        # Copyright (C) 2002 - {year} CERN
        #
        # Indico is free software; you can redistribute it and/or
        # modify it under the terms of the MIT License; see the
        # LICENSE file for more details.

    ''').lstrip().format(year=date.today().year))


def write_model(f, class_name, event):
    schema = 'events' if event else 'TODO'
    table_name = _snakify(class_name) + 's'
    if event and table_name.startswith('event_'):
        table_name = table_name[6:]
    f.write('\n\n')
    f.write(textwrap.dedent('''
        class {cls}(db.Model):
            __tablename__ = '{table}'
            __table_args__ = {{'schema': '{schema}'}}

            #: The ID of the object
            id = db.Column(
                db.Integer,
                primary_key=True
            )

            def __repr__(self):
                return format_repr(self, 'id')
    ''').lstrip().format(cls=class_name, table=table_name, schema=schema))


@click.command()
@click.option('--indico-dir', envvar='INDICO_DIR', metavar='DIR', default='indico', callback=_validate_indico_dir,
              is_eager=True, help='Path to the indico folder. Can be specified via the INDICO_DIR env var and '
                                  'defaults to `indico`')
@click.argument('name', callback=_process_name)  # adds module_dir to params
@click.option('-e', '--event', is_flag=True, help='Create module inside modules/events/ instead of modules/')
@click.option('-m', '--models', is_flag=True, help='Create models package')
@click.option('-M', '--model', 'model_classes', multiple=True, metavar='[module_name:]ClassName',
              callback=_process_model_classes,
              help='Create a model - implies `--models` and can be used multiple times. If no module name is '
                   'specified, it is derived from the class name')
@click.option('-b', '--blueprint', is_flag=True, help='Create a blueprint')
@click.option('-t', '--templates', is_flag=True, help='Add templates/ folder (only makes sense with a blueprint)')
@click.option('-c', '--controllers', is_flag=True, help='Add controllers module (only makes sense with a blueprint)')
@click.option('-v', '--views', is_flag=True, help='Add views module (only makes sense with a blueprint)')
def main(indico_dir, name, module_dir, event, models, blueprint, templates, controllers, views, model_classes):
    if not os.path.exists(module_dir):
        os.mkdir(module_dir)
        touch(os.path.join(module_dir, '__init__.py'))
    if models or model_classes:
        models_dir = os.path.join(module_dir, 'models')
        if not os.path.exists(models_dir):
            os.mkdir(models_dir)
            touch(os.path.join(models_dir, '__init__.py'))
        for module_name, class_names in model_classes.items():
            model_path = os.path.join(models_dir, f'{module_name}.py')
            if os.path.exists(model_path):
                raise click.exceptions.UsageError(f'Cannot create model in {module_name} (file already exists)')
            with open(model_path, 'w') as f:
                write_header(f)
                write(f, 'from indico.core.db import db')
                write(f, 'from indico.util.string import format_repr')
                for class_name in class_names:
                    write_model(f, class_name, event)
    if blueprint:
        blueprint_name = f'event_{name}' if event else name
        blueprint_path = os.path.join(module_dir, 'blueprint.py')
        if os.path.exists(blueprint_path):
            raise click.exceptions.UsageError('Cannot create blueprint (file already exists)')
        with open(blueprint_path, 'w') as f:
            write_header(f)
            write(f, 'from indico.web.flask.wrappers import IndicoBlueprint')
            write(f)
            if templates:
                virtual_template_folder = f'events/{name}' if event else name
                write(f, f"_bp = IndicoBlueprint('{blueprint_name}', __name__, template_folder='templates',\n\
                      virtual_template_folder='{virtual_template_folder}')")
            else:
                write(f, f"_bp = IndicoBlueprint('{blueprint_name}', __name__)")
            write(f)
    if templates:
        templates_dir = os.path.join(module_dir, 'templates')
        if not os.path.exists(templates_dir):
            os.mkdir(templates_dir)
    if controllers:
        controllers_path = os.path.join(module_dir, 'controllers.py')
        if not os.path.exists(controllers_path):
            with open(controllers_path, 'w') as f:
                write_header(f)
    if views:
        views_path = os.path.join(module_dir, 'views.py')
        if not os.path.exists(views_path):
            with open(views_path, 'w') as f:
                write_header(f)


if __name__ == '__main__':
    main()
