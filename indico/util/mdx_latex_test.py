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


def test_escape():
    assert latex_escape(r'\naughty') == r'\textbackslash{}naughty'
    assert latex_escape(r'^^5cnaughty') == r'\textbackslash{}naughty'
    assert latex_escape('^^\x1cnaughty') == r'\textbackslash{}naughty'
    assert latex_escape('^^\x1c^^.aughty') == r'\textbackslash{}\^{}\^{}.aughty'
    assert latex_escape(r'^^^^^^00005cnaughty') == r'\textbackslash{}naughty'
    assert latex_escape(r'^^^^005cnaughty') == r'\textbackslash{}naughty'
    assert (latex_escape(r'this\\is\\harmless') ==
            r'this\textbackslash{}\textbackslash{}is\textbackslash{}\textbackslash{}harmless')
    assert latex_escape(r'\\\extranaughty') == r'\textbackslash{}\textbackslash{}\textbackslash{}extranaughty'
    assert latex_escape(r'\mbox{\naughty}') == r'\textbackslash{}mbox\{\textbackslash{}naughty\}'
    assert latex_escape(r'\mbox{\^^6eaughty}') == r'\textbackslash{}mbox\{\textbackslash{}\^{}\^{}6eaughty\}'


def test_escape_math():
    assert latex_escape(r'$\naughty$') == r'\protect $\\naughty$'
    assert latex_escape(r'$\begin{naughty}$') == r'\protect $\\begin{naughty}$'
    assert latex_escape(r'$\begin{equation}$') == r'\protect $\begin{equation}$'
    assert latex_escape(r'$^^5cnaughty$') == r'\protect $\\naughty$'
    assert latex_escape('$^^\x1cnaughty$') == r'\protect $\\naughty$'
    assert latex_escape('$^^\x1c^^.aughty$') == r'\protect $\\naughty$'
    assert latex_escape(r'$^^^^^^00005cnaughty$') == r'\protect $\\naughty$'
    assert latex_escape(r'$^^^^005cnaughty$') == r'\protect $\\naughty$'
    assert latex_escape(r'$\\naughty$') == r'\protect $\\naughty$'
    assert latex_escape(r'$^^5e^5cnaughty$') == r'\protect $\\naughty$'
    assert latex_escape(r'$\to^^64ay$') == r'\protect $\\today$'
    assert latex_escape(r'$harm\\less$') == r'\protect $harm\\less$'
    assert latex_escape(r'$\\\extranaughty$') == r'\protect $\\\\extranaughty$'
    assert latex_escape(r'$\mbox{\naughty}$') == r'\protect $\mbox{\\naughty}$'
    assert latex_escape(r'$\mbox{\^^6eaughty}$') == r'\protect $\mbox{\\naughty}$'
    assert latex_escape(r'$\mbox{\very^^6eaughty}$') == r'\protect $\mbox{\\verynaughty}$'
    assert latex_escape(r'$\epsilon_\psi^\theta$') == r'\protect $\epsilon_\psi^\theta$'


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
