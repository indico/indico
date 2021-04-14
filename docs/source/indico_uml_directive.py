# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

"""
A simple Sphinx directive which extends plantweb's `directive`.

The config setting `indico_uml_prelude` can be used to include
additional plantuml code before every `indico_uml` block.
"""

from docutils.statemachine import StringList
from plantweb.directive import UmlDirective


class IndicoUMLDirective(UmlDirective):
    def run(self):
        env = self.state_machine.document.settings.env
        lines = env.config.indico_uml_prelude.split('\n')
        content = StringList()
        for n, l in enumerate(lines):
            content.append(l, source='diagram', offset=n)
        for n, l in enumerate(self.content, n + 1):
            content.append(l, source='diagram', offset=n)
        self.content = content
        return super().run()

    def _get_directive_name(self):
        return 'indico_uml'


def setup(app):
    app.add_directive('indico_uml', IndicoUMLDirective)
    app.add_config_value('indico_uml_prelude', '', True)
