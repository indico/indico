# This file is based on code taken from http://stackoverflow.com/a/18143318/298479

import os
import sys
from cStringIO import StringIO

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import string2lines


class ExecDirective(Directive):
    """Execute the specified python code and insert the output into the document"""
    has_content = True

    def run(self):
        tab_width = self.options.get('tab-width', self.state.document.settings.tab_width)
        source = self.state_machine.input_lines.source(self.lineno - self.state_machine.input_offset - 1)
        old_stdout, sys.stdout = sys.stdout, StringIO()

        try:
            exec '\n'.join(self.content)
            text = sys.stdout.getvalue()
            lines = string2lines(text, tab_width, convert_whitespace=True)
            self.state_machine.insert_input(lines, source)
            return []
        except Exception as e:
            errmsg = 'Unable to execute python code at {}:{}'.format(os.path.basename(source), self.lineno)
            return [nodes.error(None, nodes.paragraph(text=errmsg), nodes.paragraph(text=str(e)))]
        finally:
            sys.stdout = old_stdout


def setup(app):
    app.add_directive('exec', ExecDirective)
