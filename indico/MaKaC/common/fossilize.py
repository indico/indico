"""
`fossilize` allows us to "serialize" complex python objects into dictionaries and lists. Such operation is very useful for generating JSON data structures from business objects.
It works as a wrapper around `zope.interface`.

Some of the features are:
 * Different "fossil" types for the same source class;
 * Built-in inheritance support;
"""

import inspect
import re
import zope.interface


def fossilizes(*classList):
    zope.interface.declarations._implements("fossilizes", classList, zope.interface.classImplements)

def addFossil(klazz, fossils):
    """ Declares fossils for a class
    
        :param klazz: a class object
        :type klass: class object
        :param fossils: a fossil class (or a list of fossil classes)
    """
    if not type(fossils) is list:
        fossils = [fossils]

    for fossil in fossils:
        zope.interface.classImplements(klazz, fossil)

class NonFossilizableException(Exception):
    pass

class WrongFossilTypeException(Exception):
    pass

class IFossil(zope.interface.Interface):
    """
    Fossil base interface. All fossil classes should derive from this one.
    """
    pass

class Fossilizable(object):
    """
    Base class for all the objects that can be fossilized
    """

    __nameRE = re.compile('^get(.*)$')

    @classmethod
    def __extractName(cls, name):
        """ 'De-camelcase' the name """

        m = cls.__nameRE.match(name)

        if not m:
            raise Exception("method name '%s' is not valid! has to start by 'get' or use 'name' tag" % name)
        else:
            return m.group(1)[0:1].lower() + m.group(1)[1:]

    @classmethod
    def __fossilizeIterable(cls, obj, interface, **kwargs):

        if type(obj) == list:
            return map(lambda elem: cls.__fossilizeIterable(elem, interface, **kwargs), obj)
        elif type(obj) == dict:
            return dict((k,cls.__fossilizeIterable(v, interface, **kwargs)) for k,v in obj.iteritems())
        else:
            return obj.fossilize(interface, **kwargs)

    def fossilize(self, interface, **kwargs):
        """
        Fossilizes the object, using the fossil provided by `interface`.

        :param interface: the target fossile type
        :type interface: IFossil
        """

        if not interface.providedBy(self):
            raise WrongFossilTypeException("Interface '%s' not provided by '%s'" % (interface.__name__, self.__class__.__name__))

        result = {}

        for method in list(interface):

            methodResult = getattr(self, method)()
            tags = interface[method].getTaggedValueTags()

            # Result conversion
            if 'result' in tags:
                targetInterface = interface[method].getTaggedValue('result')
                #targetInterface = globals()[targetInterfaceName]
                methodResult = self.__fossilizeIterable(methodResult, targetInterface, **kwargs)

            # Conversion function
            if 'convert' in tags:
                convertFunction = interface[method].getTaggedValue('convert')
                converterArgNames = inspect.getargspec(convertFunction)[0]
                converterArgs = dict((name, kwargs[name]) for name in converterArgNames if name in kwargs)
                methodResult = convertFunction(methodResult, **converterArgs)

            # Re-name the attribute produced by the method
            if 'name' in tags:
                attrName = interface[method].getTaggedValue('name')
            else:
                attrName = self.__extractName(method)

            result[attrName] = methodResult

        return result

def fossilize(target, interface, **kwargs):
    """
    Method that allows the "fossilization" process to be called on data structures (lists, dictionaries and sets) as well as normal `Fossilizable` objects.

    :param target: target object to be fossilized
    :type target: Fossilizable
    :param interface: target fossil type
    :type interface: IFossil
    """
    if isinstance(target, Fossilizable):
        return target.fossilize(interface, **kwargs)
    else:
        t = type(target)
        if t in [int, str, float]:
            return target
        elif t in [list, set]:
            return map(lambda elem: fossilize(elem, interface, **kwargs), target)
        elif t is dict:
            return dict((k, fossilize(v, interface, **kwargs)) for k,v in target.iteritems())
        else:
            raise NonFossilizableException()

