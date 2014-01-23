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

from indico.ext.importer.recordConverter import RecordConverter
import unittest
from datetime import datetime

class RecordAddressConverterTest(RecordConverter):

    conversion = [
                  ("city",),
                  ("street", "street"),
                  ("houseNr", "nr"),
                  ]

class RecordConverterTest(RecordConverter):

    conversion = [
                  ("name",),
                  ("_surname", "surname"),
                  ("born", None, lambda x: x.strftime("%Y-%m-%d %H:%M")),
                  ("addr", "address", None, RecordAddressConverterTest),
                  ("address", "*append*", None, RecordAddressConverterTest),
                  ("card", "cardNr", lambda x: x.split(" ")[0]),
                  ("card", "cardType", lambda x: x.split(" ")[1])
                  ]

class ConverterTest(unittest.TestCase):

    def testEmptyDict(self):
        self.assertEqual(RecordConverterTest.convert({}),[{}])

    def testEmptyList(self):
        self.assertEqual(RecordConverterTest.convert([{},{}]), [{},{}])

    def testSimpleConversion(self):
        self.assertEqual(RecordConverterTest.convert({"name": "Leszek"}), [{"name": "Leszek"}])

    def testSimpleList(self):
        self.assertEqual(RecordConverterTest.convert([{"name": "Leszek"}, {"name": "Niko"}]), [{"name": "Leszek"}, {"name": "Niko"}])

    def testChangePropertyName(self):
        self.assertEqual(RecordConverterTest.convert({"_surname": "Syroka"}), [{"surname": "Syroka"}])

    def testConversionMethod(self):
        self.assertEqual(RecordConverterTest.convert({"born": datetime(1987, 3, 24, 5, 53)}), [{"born": "1987-03-24 05:53"}])

    def testAnotherConverter(self):
        self.assertEqual(RecordConverterTest.convert({"addr": {"city":"Saint Genis Pouilly", "street": "les Hautains", "houseNr": "12B"}}), \
                         [{"address": {"city":"Saint Genis Pouilly", "street": "les Hautains", "nr": "12B"}}])

    def testAppend(self):
        self.assertEqual(RecordConverterTest.convert({"address": {"city":"Saint Genis Pouilly", "street": "les Hautains", "houseNr": "12B"}}), \
                         [{"city":"Saint Genis Pouilly", "street": "les Hautains", "nr": "12B"}])

    def testMultipleProperties(self):
        self.assertEqual(RecordConverterTest.convert({'card': "1234567890 Maestro"}), [{"cardNr" : "1234567890", "cardType" : "Maestro"}])

