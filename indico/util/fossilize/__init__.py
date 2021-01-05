# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# flake8: noqa

"""
``fossilize`` allows us to "serialize" complex python objects into dictionaries
and lists. Such operation is very useful for generating JSON data structures
from business objects. It works as a wrapper around ``zope.interface``.

Some of the features are:
 * Different "fossil" types for the same source class;
 * Built-in inheritance support;
"""

import inspect
import logging
import re
import threading
from itertools import ifilter
from types import NoneType

import zope.interface


_fossil_cache = threading.local()

def fossilizes(*classList):
    """Simple wrapper around 'implements'."""
    zope.interface.declarations._implements("fossilizes",
                                            classList,
                                            zope.interface.classImplements)

def addFossil(klazz, fossils):
    """Declare fossils for a class.

    :param klazz: a class object
    :type klass: class object
    :param fossils: a fossil class (or a list of fossil classes)
    """
    if not isinstance(fossils, list):
        fossils = [fossils]

    for fossil in fossils:
        zope.interface.classImplements(klazz, fossil)


def clearCache():
    """Shortcut for Fossilizable.clearCache()"""
    Fossilizable.clearCache()


class NonFossilizableException(Exception):
    """Object is not fossilizable (doesn't implement Fossilizable)."""


class InvalidFossilException(Exception):
    """
    The fossil name doesn't follow the convention I(\w+)Fossil
    or has an invalid method name and did not declare a .name tag for it.
    """


class IFossil(zope.interface.Interface):
    """Fossil base interface.

    All fossil classes should derive from this one.
    """

class Fossilizable(object):
    """Base class for all the objects that can be fossilized."""

    __fossilNameRE = re.compile('^I(\w+)Fossil$')
    __methodNameRE = re.compile('^get(\w+)|(has\w+)|(is\w+)$')

    @classmethod
    def __extractName(cls, name):
        """
        'De-camelcase' the name
        """

        if name in _fossil_cache.methodName:
            return _fossil_cache.methodName[name]
        else:
            nmatch = cls.__methodNameRE.match(name)

            if not nmatch:
                raise InvalidFossilException("method name '%s' is not valid! "
                                             "has to start by 'get', 'has', 'is' "
                                             "or use 'name' tag" % name)
            else:
                group = nmatch.group(1) or nmatch.group(2) or nmatch.group(3)
                extractedName = group[0:1].lower() + group[1:]
                _fossil_cache.methodName[name] = extractedName
                return extractedName

    @classmethod
    def __extractFossilName(cls, name):
        """Extract the fossil name from a I(.*)Fossil class name.

        IMyObjectBasicFossil -> myObjectBasic
        """

        if name in _fossil_cache.fossilName:
            fossilName = _fossil_cache.fossilName[name]
        else:
            fossilNameMatch = Fossilizable.__fossilNameRE.match(name)
            if fossilNameMatch is None:
                raise InvalidFossilException("Invalid fossil name: %s."
                                             " A fossil name should follow the"
                                             " pattern: I(\w+)Fossil." % name)
            else:
                fossilName = fossilNameMatch.group(1)[0].lower() + \
                fossilNameMatch.group(1)[1:]

                _fossil_cache.fossilName[name] = fossilName
        return fossilName

    @classmethod
    def __obtainInterface(cls, obj, interfaceArg):
        """Obtain the appropriate interface for this object.

        :param interfaceArg: the target fossile type
        :type interfaceArg: IFossil, NoneType, or dict

        * If IFossil, we will use it.
        * If None, we will take the default fossil
        (the first one of this class's 'fossilizes' list)
        * If a dict, we will use the objects class, class name, or full class name
        as key.

        Also verify that the interface obtained through these 3 methods is
        effectively provided by the object.
        """

        if interfaceArg is None:
            # we try to take the 1st interface declared with fossilizes
            implementedInterfaces = list(
                i for i in zope.interface.implementedBy(obj.__class__) \
                if i.extends(IFossil) )

            if not implementedInterfaces:
                raise NonFossilizableException(
                    "Object %s of class %s cannot be fossilized,"
                    "no fossils were declared for it" %
                    (str(obj), obj.__class__.__name__))
            else:
                interface = implementedInterfaces[0]

        elif isinstance(interfaceArg, dict):

            className = obj.__class__.__module__ + '.' + \
                        obj.__class__.__name__

            # interfaceArg is a dictionary of class:Fossil pairs
            if className in interfaceArg:
                interface = interfaceArg[className]
            elif obj.__class__ in interfaceArg:
                interface = interfaceArg[obj.__class__]
            else:
                raise NonFossilizableException(
                    "Object %s of class %s cannot be fossilized; "
                    "its class was not a key in the provided fossils dictionary" %
                    (str(obj), obj.__class__.__name__))
        else:
            interface = interfaceArg

        return interface


    @classmethod
    def clearCache(cls):
        """Clear the fossil attribute cache."""
        _fossil_cache.methodName = {}
        _fossil_cache.fossilName = {}
        _fossil_cache.fossilInterface = {}
        _fossil_cache.fossilAttrs = {}  # Attribute Cache for Fossils with
                                        # fields that are repeated



    @classmethod
    def fossilizeIterable(cls, target, interface, useAttrCache=False, filterBy=None, **kwargs):
        """Fossilize an object, be it a 'direct' fossilizable
        object, or an iterable (dict, list, set).
        """
        if isinstance(target, Fossilizable):
            return target.fossilize(interface, useAttrCache, **kwargs)
        else:
            ttype = type(target)
            if ttype in [int, str, float, bool, NoneType]:
                return target
            elif ttype is dict:
                container = {}
                for key, value in target.iteritems():
                    container[key] = fossilize(value, interface, useAttrCache,
                                               **kwargs)
                return container
            elif hasattr(target, '__iter__'):
                if filterBy:
                    iterator = ifilter(filterBy, target)
                else:
                    iterator = iter(target)
                # we turn sets and tuples into lists since JSON does not
                # have sets / tuples
                return list(fossilize(elem,
                                      interface,
                                      useAttrCache, **kwargs) for elem in iterator)
            # If the object is a wrapper for an iterable, by default we fossilize
            # the iterable the object is wrapping. This behaviour is included in
            # order to let objects like legacy PersistentLists to be fossilized
            elif hasattr(target, '__dict__') and len(target.__dict__) == 1 and \
                     hasattr(target.__dict__.values()[0], '__iter__'):
                return list(fossilize(elem,
                                      interface,
                                      useAttrCache,
                                      **kwargs) for elem in target.__dict__.values()[0])
            elif cls.__obtainInterface(target, interface):
                return cls.fossilize_obj(target, interface, useAttrCache, **kwargs)

            else:
                raise NonFossilizableException("Type %s is not fossilizable!" %
                                               ttype)

            return fossilize(target, interface, useAttrCache, **kwargs)

    def fossilize(self, interfaceArg=None, useAttrCache=False, **kwargs):
        return self.fossilize_obj(self, interfaceArg=interfaceArg, useAttrCache=useAttrCache,
                                  **kwargs)

    @classmethod
    def fossilize_obj(cls, obj, interfaceArg=None, useAttrCache=False, mapClassType=None, **kwargs):
        """
        Fossilize the object, using the fossil provided by `interface`.

        :param interfaceArg: the target fossile type
        :type interfaceArg: IFossil, NoneType, or dict
        :param useAttrCache: use caching of attributes if same fields are
            repeated for a fossil
        :type useAttrCache: boolean
        """

        mapClassType = dict(mapClassType or {}, AvatarUserWrapper='Avatar', AvatarProvisionalWrapper='Avatar',
                            EmailPrincipal='Email')
        interface = cls.__obtainInterface(obj, interfaceArg)

        name = interface.getName()
        fossilName = cls.__extractFossilName(name)

        result = {}

        # cache method names for each interface
        names = _fossil_cache.fossilInterface.get(interface)
        if names is None:
            names = interface.names(all=True)
            _fossil_cache.fossilInterface[interface] = names
        ###

        for methodName in names:

            method = interface[methodName]

            tags = method.getTaggedValueTags()
            isAttribute = False

            if 'onlyIf' in tags:
                onlyIf = method.getTaggedValue('onlyIf')

                # If the condition not in the kwargs or the condition False, we do not fossilize the method
                if not kwargs.get(onlyIf, False):
                    continue

            # In some cases it is better to use the attribute cache to
            # speed up the fossilization
            cacheUsed = False
            if useAttrCache:
                try:
                    methodResult = _fossil_cache.fossilAttrs[obj._p_oid][methodName]
                    cacheUsed = True
                except KeyError:
                    pass
            if not cacheUsed:
                # Please use 'produce' as little as possible;
                # there is almost always a more elegant and modular solution!
                if 'produce' in tags:
                    methodResult = method.getTaggedValue('produce')(obj)
                else:
                    attr = getattr(obj, methodName)
                    if callable(attr):
                        try:
                            methodResult = attr()
                        except Exception:
                            logging.getLogger('indico.fossilize').error("Problem fossilizing '%r' with '%s'",
                                                                        obj, interfaceArg)
                            raise
                    else:
                        methodResult = attr
                        isAttribute = True

                if hasattr(obj, "_p_oid"):
                    _fossil_cache.fossilAttrs.setdefault(obj._p_oid, {})[methodName] = methodResult

            if 'filterBy' in tags:
                if 'filters' not in kwargs:
                    raise Exception('No filters defined!')
                filterName = method.getTaggedValue('filterBy')

                if filterName in kwargs['filters']:
                    filterBy = kwargs['filters'][filterName]
                else:
                    raise Exception("No filter '%s' defined!" % filterName)
            else:
                filterBy = None

            # Result conversion
            if 'result' in tags:
                targetInterface = method.getTaggedValue('result')
                #targetInterface = globals()[targetInterfaceName]

                methodResult = Fossilizable.fossilizeIterable(
                    methodResult, targetInterface, filterBy=filterBy, mapClassType=mapClassType, **kwargs)

            # Conversion function
            if 'convert' in tags:
                convertFunction = method.getTaggedValue('convert')
                converterArgNames = inspect.getargspec(convertFunction)[0]
                converterArgs = dict((name, kwargs[name])
                                     for name in converterArgNames
                                     if name in kwargs)
                if '_obj' in converterArgNames:
                    converterArgs['_obj'] = obj
                try:
                    methodResult = convertFunction(methodResult, **converterArgs)
                except Exception:
                    logging.getLogger('indico.fossilize').error("Problem fossilizing '%r' with '%s' (%s)",
                                                                obj, interfaceArg, methodName)
                    raise


            # Re-name the attribute produced by the method
            if 'name' in tags:
                attrName = method.getTaggedValue('name')
            elif isAttribute:
                attrName = methodName
            else:
                attrName = cls.__extractName(methodName)

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
                if attr not in current:
                    current[attr] = {}
                current = current[attr]

            # For the last attribute level
            current[attrList[0]] = methodResult

        if "_type" in result or "_fossil" in result:
            raise InvalidFossilException('"_type" or "_fossil"'
                                         ' cannot be a fossil attribute  name')
        else:
            result["_type"] = mapClassType.get(obj.__class__.__name__, obj.__class__.__name__)
            if fossilName:  #we check that it's not an empty string
                result["_fossil"] = fossilName
            else:
                result["_fossil"] = ""

        return result


def fossilize(target, interfaceArg=None, useAttrCache=False, **kwargs):
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
    return Fossilizable.fossilizeIterable(target, interfaceArg, useAttrCache,
                                           **kwargs)
