# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
`fossilize` allows us to "serialize" complex python objects into dictionaries
and lists. Such operation is very useful for generating JSON data structures
from business objects. It works as a wrapper around `zope.interface`.

Some of the features are:
 * Different "fossil" types for the same source class;
 * Built-in inheritance support;
"""

import inspect
import re
import zope.interface
from types import NoneType, ClassType, TypeType


def fossilizes(*classList):
    """
    Simple wrapper around 'implements'
    """
    zope.interface.declarations._implements("fossilizes",
                                            classList,
                                            zope.interface.classImplements)

def addFossil(klazz, fossils):
    """
    Declares fossils for a class

    :param klazz: a class object
    :type klass: class object
    :param fossils: a fossil class (or a list of fossil classes)
    """
    if not type(fossils) is list:
        fossils = [fossils]

    for fossil in fossils:
        zope.interface.classImplements(klazz, fossil)

def clearCache():
    """
    Shortcut for Fossilizable.clearCache()
    """
    Fossilizable.clearCache()

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
    or has an invalid method name and did not declare a .name tag for it
    """

class IFossil(zope.interface.Interface):
    """
    Fossil base interface. All fossil classes should derive from this one.
    """

class Fossilizable:
    """
    Base class for all the objects that can be fossilized
    """

    __fossilNameRE = re.compile('^I(\w+)Fossil$')
    __methodNameRE = re.compile('^get(\w+)|(has\w+)|(is\w+)$')
    __methodNameCache = {}
    __fossilNameCache = {}
    __fossilAttrsCache = {} # Attribute Cache for Fossils with
                            # fields that are repeated

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
                raise InvalidFossilException("method name '%s' is not valid! "
                                             "has to start by 'get', 'has', 'is' "
                                             "or use 'name' tag" % name)
            else:
                group = nmatch.group(1) or nmatch.group(2) or nmatch.group(3)
                extractedName = group[0:1].lower() + group[1:]
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


    def __obtainInterface(self, interfaceArg):
        """
        Obtains the appropriate interface for this object.

        :param interfaceArg: the target fossile type
        :type interfaceArg: IFossil, NoneType, or dict

            -If IFossil, we will use it.
            -If None, we will take the default fossil (the first one of this class's "fossilizes" list)
            -If a dict, we will use the object's class, class name, or full class name as key.

        Also verifies that the interface obtained through these 3 methods is effectively provided by the object.
        """
        if interfaceArg is None:
            #we try to take the 1st interface declared with fossilizes
            implementedInterfaces = list(i for i in zope.interface.implementedBy(self.__class__) if i.extends(IFossil))
            if not implementedInterfaces:
                raise NonFossilizableException("Object %s of class %s cannot be fossilized,"
                                               "no fossils were declared for it" %
                                               (str(self),
                                                self.__class__.__name__))
            else:
                interface = implementedInterfaces[0]

        elif type(interfaceArg) is dict:

            className = self.__class__.__module__ + '.' + \
                        self.__class__.__name__

            # interfaceArg is a dictionary of class:Fossil pairs
            if className in interfaceArg:
                interface = interfaceArg[className]
            else:
                raise NonFossilizableException("Object %s of class %s cannot be fossilized; "
                                               "its class was not a key in the provided fossils dictionary" %
                                               (str(self),
                                                self.__class__.__name__))
        else:
            interface = interfaceArg

        if not interface.providedBy(self):

            raise WrongFossilTypeException("Interface '%s' not provided"
                                           " by '%s'" %
                                           (interface.__name__,
                                            self.__class__.__name__))

        return interface

    @classmethod
    def clearCache(cls):
        """
        Clears the fossil attribute cache
        """
        cls.__fossilAttrsCache = {}

    @classmethod
    def _fossilizeIterable(cls, target, interface, useAttrCache = False, **kwargs):
        """
        Fossilizes an object, be it a 'direct' fossilizable
        object, or an iterable (dict, list, set);
        """

        if isinstance(target, Fossilizable):
            return target.fossilize(interface, useAttrCache, **kwargs)
        else:
            ttype = type(target)
            if ttype in [int, str, float, NoneType]:
                return target
            elif ttype is dict:
                container = {}
                for key, value in target.iteritems():
                    container[key] = fossilize(value, interface, useAttrCache, **kwargs)
                return container
            elif hasattr(target, '__iter__'):
                #we turn sets and tuples into lists since JSON does not have sets / tuples
                return list(fossilize(elem,
                                      interface,
                                      useAttrCache,
                                      **kwargs) for elem in target)
            else:
                raise NonFossilizableException("Type %s is not fossilizable!" %
                                               ttype)

            return fossilize(target, interface, useAttrCache)

    def fossilize(self, interfaceArg = None, useAttrCache = False, **kwargs):
        """
        Fossilizes the object, using the fossil provided by `interface`.

        :param interfaceArg: the target fossile type
        :type interfaceArg: IFossil, NoneType, or dict
        :param useAttrCache: use caching of attributes if same fields are
            repeated for a fossil
        :type useAttrCache: boolean
        """

        interface = self.__obtainInterface(interfaceArg)

        name = interface.getName()
        fossilName = self.__extractFossilName(name)

        result = {}

        for method in interface:

            tags = interface[method].getTaggedValueTags()

            # In some cases it is better to use the attribute cache to
            # speed up the fossilization
            cacheUsed = False
            if useAttrCache:
                try:
                    methodResult = self.__fossilAttrsCache[self._p_oid][method]
                    cacheUsed = True
                except KeyError:
                    pass
            if not cacheUsed:
                #Please use 'produce' as little as possible; there is almost always a more elegant and modular solution!
                if 'produce' in tags:
                    methodResult = interface[method].getTaggedValue('produce')(self)
                else:
                    methodResult = getattr(self, method)()

                if hasattr(self, "_p_oid"):
                    try:
                        self.__fossilAttrsCache[self._p_oid]
                    except KeyError:
                        self.__fossilAttrsCache[self._p_oid] = {}
                    self.__fossilAttrsCache[self._p_oid][method] = methodResult

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

            # In case the name contains dots, each of the 'domains' but the
            # last one are translated into nested dictionnaries. For example,
            # if we want to re-name an attribute into "foo.bar.tofu", the
            # corresponding fossilized attribute will be of the form:
            # {"foo":{"bar":{"tofu": res,...},...},...}
            # instead of:
            # {"foo.bar.tofu": res, ...}

            current = result
            attrList = attrName.split('.')

            while len(attrList) > 1:
                attr = attrList.pop(0)
                try:
                    current = current[attr]
                except KeyError:
                    current[attr] = {}
                    current = current[attr]

            # For the last attribute level
            current[attrList[0]] = methodResult

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


def fossilize(target, interfaceArg = None, useAttrCache = False, **kwargs):
    """
    Method that allows the "fossilization" process to
    be called on data structures (lists, dictionaries
    and sets) as well as normal `Fossilizable` objects.

    :param target: target object to be fossilized
    :type target: Fossilizable
    :param interfaceArg: target fossil type
    :type interfaceArg: IFossil, NoneType, or dict
    :param useAttrCache: use the attribute caching
    :type useAttrCache: boolean
    """
    return Fossilizable._fossilizeIterable(target, interfaceArg, useAttrCache, **kwargs)
