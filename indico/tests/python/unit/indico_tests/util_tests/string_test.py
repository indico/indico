# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
from indico.util.string import permissive_format, remove_extra_spaces, remove_tags, fix_broken_string


class TestPermissiveFormat(unittest.TestCase):

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
            self.assertEqual(permissive_format(text, params), result)

class TestRemoveTags(unittest.TestCase):

    def testTextRemoveExtraSpaces(self):
        texts = ["Normal text",
                 "Text     with   spaces "
                 ]
        results = ["Normal text",
                   "Text with spaces"]

        for text, result in zip(texts, results):
            self.assertEqual(remove_extra_spaces(text), result)

    def testTextRemoveTags(self):
        texts = ["There is nothing to remove",
                 "1 < 2, right?",
                 "Conference is <b>today</b>",
                 "Content is <no-valid-tag>valid</no-valid-tag>",
                 "5>3<a>Multiple</a><b>tags</b>but<c></c>1<2<d>"
                 ]
        results = ["There is nothing to remove",
                   "1 < 2, right?",
                   "Conference is today",
                   "Content is valid",
                   "5>3 Multiple tags but 1<2"
                   ]

        for text, result in zip(texts, results):
            self.assertEqual(remove_tags(text), result)


class TestDecodingEncoding(unittest.TestCase):

    def testUnicodeDecoding(self):
        string_value = "mettre à l'essai"
        self.assertEqual(string_value, u"mettre à l'essai".encode("utf-8"))

    def testFixBrokenStrings(self):
        string_value = u"mettre à l'essai".encode("latin1")
        fixed_string = fix_broken_string(string_value)
        self.assertEqual(string_value.decode("latin1").encode("utf-8"), fixed_string)
