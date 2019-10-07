# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.util.mdx_latex import latex_escape


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
