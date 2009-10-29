from MaKaC.common.fossilize import IFossil, Fossilizable, fossilizes, fossilize,\
    NonFossilizableException, WrongFossilTypeException, addFossil
import unittest

class ISomeFossil(IFossil):
    pass

class ISimpleFossil1(IFossil):
    def getB(self):
        pass

    def getC(self):
        pass
    getC.convert = lambda x: x.upper()

class ISimpleFossil2(IFossil):
    def getA(self):
        pass

    def getC(self):
        pass
    getC.convert = lambda x: x.title()

class IComplexFossil1(IFossil):
    def getSimpleInstance(self):
        pass
    getSimpleInstance.result = ISimpleFossil2

class IComplexFossil2(IFossil):
    def getSimpleInstance(self):
        pass
    getSimpleInstance.result = ISimpleFossil2
    getSimpleInstance.convert = lambda x: list(x.values())
    getSimpleInstance.name = 'mySimpleInstance'
    
class IDynamicFossil(IFossil):
    def getA(self):
        pass
    def getB(self):
        pass
    getB.convert = lambda x: x.upper()


class SimpleClass(Fossilizable):

    fossilizes(ISimpleFossil1, ISimpleFossil2)
    
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

    fossilizes(IComplexFossil1, IComplexFossil2)

    def getSimpleInstance(self):
        return SimpleClass(1,'foo','bar')
    
    
class ConversionClass(object):
    @classmethod
    def multiply(cls, number, factor):
        return number * factor
    
def sum(number, numberToBeAdded):
    return number + numberToBeAdded


class IFossilWithConversion2(IFossil):
    def getA(self):
        pass
    getA.convert = sum

class IFossilWithConversion(IFossil):
    def getA(self):
        pass
    getA.convert = ConversionClass.multiply
    def getList(self):
        pass
    getList.result = IFossilWithConversion2

class AnotherClass(Fossilizable):
    fossilizes(IFossilWithConversion)
    def __init__(self, a , list = []):
        self.a = a
        self.list = list
    def getA(self):
        return self.a
    def getList(self):
        return self.list

class AnotherChildrenClass(Fossilizable):
    fossilizes(IFossilWithConversion2)
    def __init__(self, a):
        self.a = a
    def getA(self):
        return self.a


class TestFossilize(unittest.TestCase):

    def setUp(self):
        addFossil(SimpleClass, IDynamicFossil)
        self.s = SimpleClass(1,'a','foo')
        self.c = ComplexClass()

    def testFossilizePrimitives(self):
        self.assertEquals(4, fossilize(4, ISomeFossil))
        self.assertEquals('foo', fossilize('foo', ISomeFossil))
        self.assertEquals(5.0, fossilize(5.0, ISomeFossil))

    def testFossilizeStructuresOfPrimitives(self):
        self.assertEquals([], fossilize([], ISomeFossil))
        self.assertEquals([4,[4,5,6]], fossilize([4,[4,5,6]], ISomeFossil))
        self.assertEquals({'a':'foo', 2:'bar'}, fossilize({'a':'foo', 2:'bar'}, ISomeFossil))
        self.assertEquals({'a':'foo', 2:'bar', 3:5.0}, fossilize({'a':'foo', 2:'bar', 3:5.0}, ISomeFossil))

    def testFossilizingNonFossilizable(self):
        self.assertRaises(NonFossilizableException, fossilize, 1+4j, ISomeFossil)

    def testFossilizingWrongType(self):
        self.assertRaises(WrongFossilTypeException, self.s.fossilize, ISomeFossil)

    def testFossilizingSimpleClass(self):
        self.assertEquals(self.s.fossilize(ISimpleFossil1),
                          {"b": "a", "c":"FOO"})
        self.assertEquals(self.s.fossilize(ISimpleFossil2),
                          {"a":1, "c":"Foo"})

    def testFossilizingComplexClass(self):
        self.assertEquals(self.c.fossilize(IComplexFossil1),
                          {'simpleInstance': {'a': 1, 'c':'Bar'}})

    def testFossilizingComplexClassWithConversion(self):
        self.assertEquals(self.c.fossilize(IComplexFossil2),
                          {'mySimpleInstance': [1,'Bar']})

    def testFossilizingWithInheritance(self):
        d = DerivedClass(2,'b','bar')
        self.assertEquals(d.fossilize(ISimpleFossil1),
                          {"b": "b", "c":"BAR"})
        
    def testFossilizeList(self):
        d1 = SimpleClass(1, 'a', 'aaa')
        d2 = SimpleClass(2, 'b', 'bbb')
        l = [d1, d2]
        self.assertEquals(fossilize(l, ISimpleFossil1),
                          [{'b': 'a', 'c': 'AAA'}, {'b': 'b', 'c': 'BBB'}] )
        
    def testFossilizingWithDynamicFossil(self):
        d = DerivedClass(2, 'bababa', 'bar')
        self.assertEquals(d.fossilize(ISimpleFossil1),
                          {"b": "bababa", "c":"BAR"})
        self.assertEquals(d.fossilize(IDynamicFossil),
                          {"a": 2, "b":"BABABA"})
        
    def testFossilizingWithConversion(self):
        a1 = AnotherChildrenClass(10)
        a2 = AnotherChildrenClass(20)
        aFather = AnotherClass(1000, [a1, a2])
        self.assertEquals(aFather.fossilize(IFossilWithConversion, factor = 10, numberToBeAdded = 1),
                          {'a': 10000, 'list': [{'a': 11}, {'a': 21}]})


if __name__ == '__main__':
    unittest.main()
