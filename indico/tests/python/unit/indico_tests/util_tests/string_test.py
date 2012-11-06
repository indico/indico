# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Tests for `indico.util.string` module
"""

import unittest
from indico.util.string import formatParentheses

class TestFormatParentheses(unittest.TestCase):

    def testTextParenthesesFormatting(self):
        params = dict(url="www.cern.ch", name="My Name", other="Nothing")
        texts = ["This is a text without parameters.",
                 "This is the url: {url} and name: {name}} and url: {url} one more time",
                 "This text contains missing parentheses: {url}{url} {url name}",
                 "This text contains missing parentheses: {name}} {} }{test{}}}",
                 "This text contains unused parameters: {one}{name}{two}",
                 "Parameter inside parameter: {url{url}}",
                 ]
        results = ["This is a text without parameters.",
                   "This is the url: www.cern.ch and name: My Name} and url: www.cern.ch one more time",
                   "This text contains missing parentheses: www.cern.chwww.cern.ch {url name}",
                   "This text contains missing parentheses: My Name} {} }{test{}}}",
                   "This text contains unused parameters: {one}My Name{two}",
                   "Parameter inside parameter: {urlwww.cern.ch}",
                   ]

        for text, result in zip(texts, results):
            self.assertEqual(formatParentheses(text, params), result)
