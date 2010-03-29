"""
`fossilize` allows us to "serialize" complex python
objects into dictionaries and lists. Such operation
is very useful for generating JSON data structures
from business objects.
It works as a wrapper around `zope.interface`.

Some of the features are:
 * Different "fossil" types for the same source class;
 * Built-in inheritance support;
"""

import inspect
import re
import zope.interface


def fossilizes(*classList):
    """
    Simple wrapper around 'implements'
    """
    zope.interface.declarations._implements("fossilizes",
                                            classList,
                                            zope.interface.classImplements)

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
    """
    Object is not fossilizable (doesn't implement Fossilizable)
    """

class WrongFossilTypeException(Exception):
    """
    Fossil type doesn't apply to target object
    """

class InvalidFossilException(Exception):
    """
    The fossil name doesn't follow the convention I(\w+)Fossil
    """

class IFossil(zope.interface.Interface):
    """
    Fossil base interface. All fossil classes should derive from this one.
    """

class Fossilizable(object):
    """
    Base class for all the objects that can be fossilized
    """

    __fossilNameRE = re.compile('^I(\w+)Fossil$')
    __methodNameRE = re.compile('^get(\w+)$')
    __methodNameCache = {}
    __fossilNameCache = {}

    @classmethod
    def __extractName(cls, name):
        """
        'De-camelcase' the name
        """

        if name in cls.__methodNameCache:
            return cls.__methodNameCache[name]
        else:
            nmatch = cls.__methodNameRE.match(name)

            if not nmatch:
                raise Exception("method name '%s' is not valid!"
                                " has to start by 'get' or use "
                                "'name' tag" % name)
            else:
                extractedName = nmatch.group(1)[0:1].lower() + \
                                nmatch.group(1)[1:]
                cls.__methodNameCache[name] = extractedName
                return extractedName

    @classmethod
    def __extractFossilName(cls, name):
        """
        Extracts the fossil name from a I(.*)Fossil
        class name.
        IMyObjectBasicFossil -> myObjectBasic
        """

        if name in cls.__fossilNameCache:
            fossilName = cls.__fossilNameCache[name]
        else:
            fossilNameMatch = Fossilizable.__fossilNameRE.match(name)
            if fossilNameMatch is None:
                raise InvalidFossilException("Invalid fossil name: %s."
                                             " A fossil name should follow the"
                                             " pattern: I(\w+)Fossil." % name)
            else:
                fossilName = fossilNameMatch.group(1)[0].lower() + fossilNameMatch.group(1)[1:]
                cls.__fossilNameCache[name] = fossilName
        return fossilName


    @classmethod
    def _fossilizeIterable(cls, target, interface, **kwargs):
        """
        Fossilizes an object, be it a 'direct' fossilizable
        object, or an iterable (dict, list, set);
        """

        if isinstance(target, Fossilizable):
            return target.fossilize(interface, **kwargs)
        else:
            ttype = type(target)
            if ttype in [int, str, float]:
                return target
            elif ttype in [list, set]:
                container = ttype()
                for elem in target:
                    container.append(fossilize(elem, interface, **kwargs))
                return container
            elif ttype is dict:
                container = {}
                for key, value in target.iteritems():
                    container[key] = fossilize(value, interface, **kwargs)
                return container
            else:
                raise NonFossilizableException()

            return fossilize(target, interface)

    def fossilize(self, interface, **kwargs):
        """
        Fossilizes the object, using the fossil provided by `interface`.

        :param interface: the target fossile type
        :type interface: IFossil
        """

        if not interface.providedBy(self):
            raise WrongFossilTypeException("Interface '%s' not provided"
                                           " by '%s'" %
                                           (interface.__name__,
                                            self.__class__.__name__))

        name = interface.getName()
        fossilName = self.__extractFossilName(name)

        result = {}

        for method in interface:

            methodResult = getattr(self, method)()
            tags = interface[method].getTaggedValueTags()

            # Result conversion
            if 'result' in tags:
                targetInterface = interface[method].getTaggedValue('result')
                #targetInterface = globals()[targetInterfaceName]
                methodResult = Fossilizable._fossilizeIterable(
                    methodResult, targetInterface, **kwargs)

            # Conversion function
            if 'convert' in tags:
                convertFunction = interface[method].getTaggedValue('convert')
                converterArgNames = inspect.getargspec(convertFunction)[0]
                converterArgs = dict((name, kwargs[name])
                                     for name in converterArgNames
                                     if name in kwargs)
                methodResult = convertFunction(methodResult, **converterArgs)

            # Re-name the attribute produced by the method
            if 'name' in tags:
                attrName = interface[method].getTaggedValue('name')
            else:
                attrName = self.__extractName(method)

            result[attrName] = methodResult

        if "_type" in result or "_fossil" in result:
            raise InvalidFossilException('"_type" or "_fossil"'
                                         ' cannot be a fossil attribute  name')
        else:
            result["_type"] = self.__class__.__name__
            if fossilName: #we check that it's not an empty string
                result["_fossil"] = fossilName
            else:
                result["_fossil"] = ""

        return result

def fossilize(target, interface, **kwargs):
    """
    Method that allows the "fossilization" process to
    be called on data structures (lists, dictionaries
    and sets) as well as normal `Fossilizable` objects.

    :param target: target object to be fossilized
    :type target: Fossilizable
    :param interface: target fossil type
    :type interface: IFossil
    """
    return  Fossilizable._fossilizeIterable(target, interface, **kwargs)
