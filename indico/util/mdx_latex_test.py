# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# ruff: noqa: E501

import pytest
from markdown import Markdown

from indico.util.mdx_latex import LaTeXExtension, _resolve_latex_carets, latex_escape


@pytest.mark.parametrize(('input', 'expected'), (
    (r'\naughty', r'\textbackslash{}naughty'),
    (r'^^5cnaughty', r'\textbackslash{}naughty'),
    ('^^\x1cnaughty', r'\textbackslash{}naughty'),
    ('^^\x1c^^.aughty', r'\textbackslash{}\^{}\^{}.aughty'),
    (r'^^^^^^00005cnaughty', r'\textbackslash{}naughty'),
    (r'^^^^005cnaughty', r'\textbackslash{}naughty'),
    (r'this\\is\\harmless', r'this\textbackslash{}\textbackslash{}is\textbackslash{}\textbackslash{}harmless'),
    (r'\\\extranaughty', r'\textbackslash{}\textbackslash{}\textbackslash{}extranaughty'),
    (r'\mbox{\naughty}', r'\textbackslash{}mbox\{\textbackslash{}naughty\}'),
    (r'\mbox{\^^6eaughty}', r'\textbackslash{}mbox\{\textbackslash{}\^{}\^{}6eaughty\}'),
))
def test_escape(input, expected):
    assert latex_escape(input) == expected


@pytest.mark.parametrize(('input', 'expected'), (
    (r'\naughty', r'\protect $\\naughty$'),
    (r'\begin{naughty}', r'\protect $\\begin{naughty}$'),
    (r'\begin{equation}', r'\protect $\begin{equation}$'),
    (r'^^5cnaughty', r'\protect $\\naughty$'),
    ('^^\x1cnaughty', r'\protect $\\naughty$'),
    ('^^\x1c^^.aughty', r'\protect $\\naughty$'),
    (r'^^^^^^00005cnaughty', r'\protect $\\naughty$'),
    (r'^^^^005cnaughty', r'\protect $\\naughty$'),
    (r'\\naughty', r'\protect $\\naughty$'),
    (r'^^5e^5cnaughty', r'\protect $\\naughty$'),
    (r'\to^^64ay', r'\protect $\\today$'),
    (r'harm\\less', r'\protect $harm\\less$'),
    (r'\\\extranaughty', r'\protect $\\\\extranaughty$'),
    (r'\mbox{\naughty}', r'\protect $\mbox{\\naughty}$'),
    (r'\mbox{\^^6eaughty}', r'\protect $\mbox{\\naughty}$'),
    (r'\mbox{\very^^6eaughty}', r'\protect $\mbox{\\verynaughty}$'),
    (r'\epsilon_\psi^\theta', r'\protect $\epsilon_\psi^\theta$'),
))
def test_escape_math(input, expected):
    assert latex_escape(f'${input}$') == expected


@pytest.mark.parametrize(('input', 'expected'), (
    (r'\^^4oday we are ^^5cnaughty \^^4aday', r'\today we are \naughty \Jday'),
    (r'\^^4aday we are ^^5cnaughty \^^4oday', r'\Jday we are \naughty \today'),
    (r'\^^4aday we are ^^5cnaughty \^^4aday', r'\Jday we are \naughty \Jday'),
    (r'\^^4oday', r'\today'),
    (r'^^5e^5ctoday', r'\today'),
    (r'^^5cnaughty', r'\naughty'),
    ('^^\x1cnaughty', r'\naughty'),
    ('^^\x1c^^.aughty', r'\naughty'),
    (r'^^^^^^00005cnaughty', r'\naughty'),
    (r'^^^^^^00x05cnaughty', r'00x05cnaughty'),
    (r'^^^^00x05cnaughty', r'^00x05cnaughty'),
    (r'^^^^^^10ffff', '\U0010ffff'),
    (r'^^^^^^110000', ''),
))
def test_resolve_carets(input, expected):
    assert _resolve_latex_carets(input) == expected


@pytest.mark.parametrize(('input', 'expected'), (
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
))
def test_convert_markdown_to_latex(input, expected):
    md = Markdown(safe_mode='remove')
    _latex_md = LaTeXExtension(configs={'apply_br': True})
    _latex_md.extendMarkdown(md, md.__dict__)
    assert md.convert(input) == expected
