#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from os import path


PLACEHOLDER = '/*-- ICONS --*/'

indico_root = path.abspath(path.join(path.dirname(path.abspath(__file__)), '..', '..'))
web_dir = path.join(indico_root, 'indico', 'web')
stylesheet_dir = path.join(web_dir, 'client', 'styles', 'partials')
stylesheet_template = path.join(stylesheet_dir, '_icons.in')
stylesheet_output = path.join(stylesheet_dir, '_icons.scss')
selection_file = path.join(web_dir, 'static', 'fonts', 'icomoon', 'selection.json')

# Read the selection file and get the icon names

with open(selection_file) as f:
    selection = json.loads(f.read())

icons = [
    (
        i['properties']['name'].split(',', 1)[0].lower().replace('_', '-'),
        i['properties']['code']
    )
    for i in selection['icons']
]
icons.sort(key=lambda x: x[0])

# Generate the icon list

SCSS_TEMPLATE = '''
.icon-{0}::before,
%icon-{0} {{
  content: '\\{1}';
}}
'''.strip()
icon_list_scss = '\n'.join([
    SCSS_TEMPLATE.format(i[0], format(i[1], 'x'))
    for i in icons
])

# Generate the final SCSS file

with open(stylesheet_template) as f:
    final_scss = f.read().replace(PLACEHOLDER, icon_list_scss)

with open(stylesheet_output, mode='w') as f:
    f.write(final_scss)

print(f'Written {stylesheet_output}')
