# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from indico.util import mdx_latex
from markdown import Markdown
import pytest


_md = Markdown(safe_mode='remove')
_latex_md = mdx_latex.LaTeXExtension()
_latex_md.extendMarkdown(_md, _md.__dict__)


@pytest.mark.parametrize(('input', 'expected'), [
    ('\nplain text\n', 'plain text'),
    ('plain text with reserved characters &^{}', r'plain text with reserved characters \&\^{}\{\}'),
    ('**bold text**', r'\textbf{bold text}'),
    ('**bold with &reserved{} characters**', r'\textbf{bold with \&reserved\{\} characters}'),
    ('*italic text*', r'\emph{italic text}'),
    ('*italic text with reserved chars &{}*', r'\emph{italic text with reserved chars \&\{\}}'),
    ('[link with reserved chars&{}](http://indico.github.io)', r'\href{http://indico.github.io}{link with reserved chars\&\{\}}'),
    ('> Plain Blockquote', '\\begin{quotation}\nPlain Blockquote\n\\end{quotation}'),
    ('> Blockquote with reserved chars &{}', '\\begin{quotation}\nBlockquote with reserved chars \&\{\}\n\\end{quotation}'),
    ('\tPlain code sample', '\\begin{verbatim}\nPlain code sample\n\\end{verbatim}'),
    ('\tCode sample with reserved chars &{}', '\\begin{verbatim}\nCode sample with reserved chars &{}\n\\end{verbatim}'),
    ('## Plain Heading ##', '\subsection{Plain Heading}'),
    ('## Heading with reserved chars &{} ##', '\subsection{Heading with reserved chars \&\{\}}'),
])
def test_convert_markdown_to_latex(input, expected):
    assert _md.convert(input) == expected
