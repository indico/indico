# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import pytest
from markdown import Markdown

from indico.util.mdx_latex import LaTeXExtension, latex_escape


def test_escape():
    assert latex_escape(r'\naughty') == r'\textbackslash{}naughty'
    assert (latex_escape(r'this\\is\\harmless') ==
            r'this\textbackslash{}\textbackslash{}is\textbackslash{}\textbackslash{}harmless')
    assert latex_escape(r'\\\extranaughty') == r'\textbackslash{}\textbackslash{}\textbackslash{}extranaughty'


def test_escape_math():
    assert latex_escape(r'$\naughty$') == r'\protect $\\naughty$'
    assert latex_escape(r'$\\naughty$') == r'\protect $\\naughty$'
    assert latex_escape(r'$harm\\less$') == r'\protect $harm\\less$'
    assert latex_escape(r'$\\\extranaughty$') == r'\protect $\\\\extranaughty$'


@pytest.mark.parametrize(('input', 'expected'), [
    ('\nplain text\n', 'plain text'),
    ('plain text with reserved characters &^{}', r'plain text with reserved characters \&\^{}\{\}'),
    ('**bold text**', r'\textbf{bold text}'),
    ('**bold with &reserved{} characters**', r'\textbf{bold with \&reserved\{\} characters}'),
    ('*italic text*', r'\emph{italic text}'),
    ('*italic text with reserved chars &{}*', r'\emph{italic text with reserved chars \&\{\}}'),
    ('[link with reserved chars&{}](http://indico.github.io)', r'\href{http://indico.github.io}{link with reserved chars\&\{\}}'),
    ('> Plain Blockquote', '\\begin{quotation}\nPlain Blockquote\n\\end{quotation}'),
    ('> Blockquote with reserved chars &{}', '\\begin{quotation}\nBlockquote with reserved chars \\&\\{\\}\n\\end{quotation}'),
    ('\tPlain code sample', '\\begin{verbatim}\nPlain code sample\n\\end{verbatim}'),
    ('\tCode sample with reserved chars &{}', '\\begin{verbatim}\nCode sample with reserved chars \\&\\{\\}\n\\end{verbatim}'),
    ('## Plain Heading ##', r'\subsection{Plain Heading}'),
    ('## Heading with reserved chars &{} ##', r'\subsection{Heading with reserved chars \&\{\}}'),
])
def test_convert_markdown_to_latex(input, expected):
    md = Markdown(safe_mode='remove')
    _latex_md = LaTeXExtension(configs={'apply_br': True})
    _latex_md.extendMarkdown(md, md.__dict__)
    assert md.convert(input) == expected
