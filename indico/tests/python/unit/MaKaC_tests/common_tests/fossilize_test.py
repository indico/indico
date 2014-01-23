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

# For now, disable Pylint
# pylint: disable-all


from MaKaC.common.fossilize import IFossil, Fossilizable, fossilizes, fossilize, \
    NonFossilizableException, addFossil,\
    InvalidFossilException
import unittest

class ISomeFossil(IFossil):
    pass

class ISimpleFossil1Fossil(IFossil):
    def getB(self):
        pass

    def getC(self):
        pass
    getC.convert = lambda x: x.upper()

class ISimpleFossil2Fossil(IFossil):
    def getA(self):
        pass

    def getC(self):
        pass
    getC.convert = lambda x: x.title()

class IComplexFossil1Fossil(IFossil):
    def getSimpleInstance(self):
        pass
    getSimpleInstance.result = ISimpleFossil2Fossil

class IComplexFossil2Fossil(IFossil):
    def getSimpleInstance(self):
        pass
    getSimpleInstance.result = ISimpleFossil2Fossil
    getSimpleInstance.convert = lambda x: sorted(x.values())
    getSimpleInstance.name = 'mySimpleInstance'

class IDynamicFossil(IFossil):
    def getA(self):
        pass
    def getB(self):
        pass
    getB.convert = lambda x: x.upper()

class IFossilWithProduceFossil(ISimpleFossil1Fossil):

    def getSum(self):
        pass
    getSum.produce = lambda self: self.a + self.b

class IAttributeFossil(IFossil):
    def a(self):
        pass
    def b(self):
        pass
    def c(self):
        pass

class IClassWithDifferentMethodNamesFossil(IFossil):
    def getAttributeOne(self):
        pass
    def hasAttributeTwo(self):
        pass
    def isAttributeThree(self):
        pass
    def weirdMethodName(self):
        pass
    weirdMethodName.name = 'weirdName'



class IClassWithDifferentMethodNamesBadFossil(IClassWithDifferentMethodNamesFossil):
    def weirdMethodName(self):
        pass

class IClassWithDifferentMethodNamesBad2Fossil(IClassWithDifferentMethodNamesFossil):
    def get_type(self):
        pass


class SimpleClass(Fossilizable):

    fossilizes(ISimpleFossil1Fossil, ISimpleFossil2Fossil, IFossilWithProduceFossil, IAttributeFossil)

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def getA(self):
        return self.a

    def getB(self):
        return self.b

    def getC(self):
        return self.c


class DerivedClass(SimpleClass):
    pass


class ComplexClass(Fossilizable):

    def __init__(self):
        self.simpleInstance = SimpleClass(1, 'foo', 'bar')

    fossilizes(IComplexFossil1Fossil, IComplexFossil2Fossil)

    def getSimpleInstance(self):
        return self.simpleInstance


class IterableWrapper(object):
    def __init__(self, *content):
        self.onlyAttribute = list(content)


class ConversionClass(object):
    @classmethod
    def multiply(cls, number, factor):
        return number * factor


def mysum(number, numberToBeAdded):
    return number + numberToBeAdded


class IWithConversion2Fossil(IFossil):
    def getA(self):
        pass
    getA.convert = mysum


class IWithConversionFossil(IFossil):
    def getA(self):
        pass
    getA.convert = ConversionClass.multiply
    def getList(self):
        pass
    getList.result = IWithConversion2Fossil


class AnotherClass(Fossilizable):
    fossilizes(IWithConversionFossil)
    def __init__(self, a , listArg):
        self.a = a
        self.list = listArg
    def getA(self):
        return self.a
    def getList(self):
        return self.list

class AnotherChildrenClass(Fossilizable):
    fossilizes(IWithConversion2Fossil)
    def __init__(self, a):
        self.a = a
    def getA(self):
        return self.a


class ClassWithDifferentMethodNames(Fossilizable):
    fossilizes(IClassWithDifferentMethodNamesFossil, IClassWithDifferentMethodNamesBadFossil, IClassWithDifferentMethodNamesBad2Fossil)
    def __init__(self):
        pass
    def getAttributeOne(self):
        return 1
    def hasAttributeTwo(self):
        return 2
    def isAttributeThree(self):
        return 3
    def weirdMethodName(self):
        return 4
    def get_type(self):
        pass


class TestFossilize(unittest.TestCase):

    def setUp(self):
        addFossil(SimpleClass, IDynamicFossil)
        self.s = SimpleClass(1, 'a', 'foo')
        self.c = ComplexClass()

    def testFossilizePrimitives(self):
        "Serializing primitive objects such as strings, integers and floats"

        self.assertEquals(4, fossilize(4, ISomeFossil))
        self.assertEquals('foo', fossilize('foo', ISomeFossil))
        self.assertEquals(5.0, fossilize(5.0, ISomeFossil))
        self.assertEquals(None, fossilize(None, ISomeFossil))

    def testFossilizeStructuresOfPrimitives(self):
        "Serializing semi-structured data such as lists and dictionaries"

        self.assertEquals([], fossilize([], ISomeFossil))
        self.assertEquals([4, [4, 5, 6], [1]], fossilize([4, (4, 5, 6), set([1])], ISomeFossil))
        self.assertEquals({'a':'foo', 2:'bar'}, fossilize({'a':'foo', 2:'bar'}, ISomeFossil))
        self.assertEquals({'a':'foo', 2:'bar', 3:5.0}, fossilize({'a':'foo', 2:'bar', 3:5.0}, ISomeFossil))

    def testFossilizeNames(self):
        "Method names should map to attribute names"

        o1 = ClassWithDifferentMethodNames()
        self.assertEquals(o1.fossilize(IClassWithDifferentMethodNamesFossil), {'isAttributeThree': 3, 'attributeOne': 1, '_type': 'ClassWithDifferentMethodNames', 'weirdName': 4, 'hasAttributeTwo': 2, '_fossil': 'classWithDifferentMethodNames'})

    def testInvalidNames(self):
        "Some invalid names should raise an exception"

        o1 = ClassWithDifferentMethodNames()
        self.assertRaises(InvalidFossilException, fossilize, o1, IClassWithDifferentMethodNamesBadFossil)
        self.assertRaises(InvalidFossilException, fossilize, o1, IClassWithDifferentMethodNamesBad2Fossil)

    def testFossilizingNonFossilizable(self):
        "Non-Fossilizable objects should be OK to fossilize"

        self.assertEqual(fossilize(1+4j, ISomeFossil), {'_fossil': 'some', '_type': 'complex'})

    def testFossilizingWrongType(self):
        "Fossilizing Fossilizables using non-standard types should be OK"

        self.assertEqual(self.s.fossilize(ISomeFossil), {'_fossil': 'some', '_type': 'SimpleClass'})

    def testFossilizingSimpleClass(self):
        "Simple fossilization example"

        self.assertEquals(self.s.fossilize(ISimpleFossil1Fossil),
                          {'_type':'SimpleClass', '_fossil':'simpleFossil1', "b": "a", "c":"FOO"})
        self.assertEquals(self.s.fossilize(ISimpleFossil2Fossil),
                          {'_type':'SimpleClass', '_fossil':'simpleFossil2', "a":1, "c":"Foo"})

    def testFossilizingComplexClass(self):
        "Complex fossilization example"

        self.assertEquals(self.c.fossilize(IComplexFossil1Fossil),
                          {'_type':'ComplexClass', '_fossil':'complexFossil1', 'simpleInstance': {'_type':'SimpleClass', '_fossil':'simpleFossil2', 'a': 1, 'c':'Bar'}})

    def testFossilizingComplexClassWithConversion(self):
        "Complex fossilization example including conversion"

        self.assertEquals(self.c.fossilize(IComplexFossil2Fossil),
                          {'_type':'ComplexClass', '_fossil':'complexFossil2', 'mySimpleInstance': [1, 'Bar', 'SimpleClass', 'simpleFossil2']})

    def testFossilizingWithInheritance(self):
        "Fossil inheritance"

        d = DerivedClass(2, 'b', 'bar')
        self.assertEquals(d.fossilize(ISimpleFossil1Fossil),
                          {"_type": "DerivedClass", "_fossil": "simpleFossil1", "b": "b", "c":"BAR"})

    def testFossilizeList(self):
        "Fossilize list of fossilizable classes"

        d1 = SimpleClass(1, 'a', 'aaa')
        d2 = SimpleClass(2, 'b', 'bbb')
        l = [d1, d2]
        self.assertEquals(fossilize(l, ISimpleFossil1Fossil),
                          [{'_type':'SimpleClass', '_fossil':'simpleFossil1', 'b': 'a', 'c': 'AAA'}, {'_type':'SimpleClass', '_fossil':'simpleFossil1', 'b': 'b', 'c': 'BBB'}] )

    def testFossilizingWithDynamicFossil(self):
        "Dynamic (added in runtime) fossils"

        d = DerivedClass(2, 'bababa', 'bar')
        self.assertEquals(d.fossilize(ISimpleFossil1Fossil),
                          {'_type':'DerivedClass', '_fossil':'simpleFossil1', "b": "bababa", "c":"BAR"})
        self.assertEquals(d.fossilize(IDynamicFossil),
                          {'_type':'DerivedClass', '_fossil':'dynamic', "a": 2, "b":"BABABA"})

    def testFossilizingWithConversion(self):
        "Fossilize composite objects with conversion"

        a1 = AnotherChildrenClass(10)
        a2 = AnotherChildrenClass(20)
        aFather = AnotherClass(1000, [a1, a2])
        self.assertEquals(aFather.fossilize(IWithConversionFossil, factor = 10, numberToBeAdded = 1),
                          {'_type':'AnotherClass', '_fossil':'withConversion', 'a': 10000, 'list': [{'_type': 'AnotherChildrenClass', '_fossil': 'withConversion2', 'a': 11}, {'_type': 'AnotherChildrenClass', '_fossil': 'withConversion2', 'a': 21}]})

    def testFossilizeProduce(self):
        "'produce' attribute"

        s1 = SimpleClass(10, 20, 'foo')
        self.assertEquals(s1.fossilize(IFossilWithProduceFossil),
                          {'_type': 'SimpleClass', '_fossil': 'fossilWithProduce', 'sum': 30, 'b': 20, 'c': 'FOO'})

    def testFossilizeIterableWrapper(self):
        "Iterable wrapper (legacy PersistentList, etc...)"

        s1 = SimpleClass(10, 20, 'foo')
        iterWrap = IterableWrapper(s1)
        self.assertEquals(fossilize(iterWrap),
                          [{'_fossil': 'simpleFossil1', 'c': 'FOO', 'b': 20, '_type': 'SimpleClass'}])


    def testFossilizeDefault(self):
        "Default fossil"

        s1 = SimpleClass(10, 20, 'foo')
        d1 = DerivedClass(10, 50, 'bar')
        self.assertEquals(s1.fossilize(), {'_type':'SimpleClass', '_fossil':'simpleFossil1', "b": 20, "c":"FOO"})
        self.assertEquals(fossilize(d1), {'_type':'DerivedClass', '_fossil':'simpleFossil1', "b": 50, "c":"BAR"})
        self.assertEquals(fossilize([s1, d1]), [fossilize(s1), d1.fossilize()])

    def testFossilizeDict(self):
        "Fossilize using a dictionary of interfaces"

        s1 = SimpleClass(10, 20, 'foo')
        d1 = DerivedClass(10, 50, 'bar')
        self.assertEquals(fossilize([s1, d1], {"indico.tests.python.unit.MaKaC_tests.common_tests.fossilize_test.SimpleClass": ISimpleFossil2Fossil, "indico.tests.python.unit.MaKaC_tests.common_tests.fossilize_test.DerivedClass": ISimpleFossil1Fossil}),
                          [s1.fossilize(ISimpleFossil2Fossil), d1.fossilize(ISimpleFossil1Fossil)])

    def testFossilizeWrongDict(self):
        "Fossilize using a wrong dictionary of interfaces"

        s1 = SimpleClass(10, 20, 'foo')
        d1 = DerivedClass(10, 50, 'bar')
        self.assertRaises(NonFossilizableException, fossilize, [s1, d1],
                          {"indico.tests.python.unit.MaKaC_tests.common_tests.fossilize_test.DerivedClass": ISimpleFossil1Fossil})

    def testFossilizeWithAttributes(self):
        """
        Using attributes instead of getters
        """
        s1 = SimpleClass(10, 20, 'foo')
        d1 = DerivedClass(10, 50, 'bar')
        self.assertEquals(s1.fossilize(IAttributeFossil), {'_type':'SimpleClass', '_fossil':'attribute', "a": 10, "b": 20, "c":"foo"})
        self.assertEquals(fossilize(d1, IAttributeFossil), {'_type':'DerivedClass', '_fossil':'attribute', "a": 10, "b": 50, "c":"bar"})
