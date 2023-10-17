#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from pathlib import Path


PLACEHOLDER = '/*-- ICONS --*/'

indico_root = Path(__file__).parents[2]
web_dir = indico_root / 'indico' / 'web'
selection_file = web_dir / 'static' / 'fonts' / 'icomoon' / 'selection.json'
stylesheet_dir = web_dir / 'client' / 'styles' / 'partials'
stylesheet_template = stylesheet_dir / '_icons.in'
stylesheet_output = stylesheet_dir / '_icons.scss'

# Read the selection file and get the icon names
selection = json.loads(selection_file.read_text())
icons = sorted(
    (
        icon['properties']['name'].split(',', 1)[0].lower().replace('_', '-'),
        icon['properties']['code']
    )
    for icon in selection['icons']
)

# Generate the icon list
SCSS_TEMPLATE = '''
.icon-{name}::before,
%icon-{name} {{
  content: '\\{code:x}';
}}
'''.strip()
icon_list_scss = '\n'.join(SCSS_TEMPLATE.format(name=icon[0], code=icon[1]) for icon in icons)

# Generate the final SCSS file
final_scss = stylesheet_template.read_text().replace(PLACEHOLDER, icon_list_scss)
stylesheet_output.write_text(final_scss)

print(f'Written {stylesheet_output}')
