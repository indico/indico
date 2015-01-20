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

import copy
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

from MaKaC.common.Conversion import Conversion

globals()['_PickleJar__mappings_pickle'] = {}
globals()['_PickleJar__mappings_unpickle'] = {}

globalPickleMap = globals()['_PickleJar__mappings_pickle']
globalUnpickleMap = globals()['_PickleJar__mappings_unpickle']

def if_else(cond, resT, resF):
    if cond:
        return resT
    else:
        return resF

class PicklerException(Exception):
    def __init__(self, message, inner=None):
        self.message = message
        self.inner = inner

    def __str__(self):
        return str(self.message) + "\r\n" + str(self.inner)

def functional_append(list, element):
    newlist = copy.deepcopy(list)
    newlist.append(element)
    return newlist

def stringToBool(s):
    if (s.lower() == 'false'):
        return False
    elif (s.lower() == 'true'):
        return True
    else:
        raise ValueError('Impossible to convert \'%s\' to bool' % s)

def classPath(clazz):
    return "%s.%s" % (clazz.__module__, clazz.__name__)


def setProp(root, property, method, modifier, isPicklableObject = False):
    if len(property) == 1:
        if method.__name__ == '__init__':
            root[property[0]] = (None, modifier, isPicklableObject)
        else:
            root[property[0]] = (method,modifier, isPicklableObject)
    else:
        if not root.has_key(property[0]):
            root[property[0]] = PickleTree({})
        setProp(root[property[0]], property[1:], method, modifier, isPicklableObject)

class PropIterator:
    def __init__(self, root):
        self.__stack = [([],root)]

    def __findNext(self):

        elem = self.__stack[-1]

        if elem[1].__class__ != PickleTree:
            self.__stack.pop()
            return elem
        else:
            (path,root) = self.__stack.pop()

            self.__stack.extend(map(lambda x: (functional_append(path,x[0]), x[1]),
                                    root.iteritems()))
            return self.__findNext()

    def next(self):
        try:
            (path,elem) = self.__stack[-1]
        except:
            raise StopIteration()

        if type(elem) == 'tuple':
            return (path, elem)
        else:
            return self.__findNext()

class PickleTree:
    def __init__(self, root):
        self.__root = root

    def __getitem__(self, key):
        return self.__root[key]

    def __setitem__(self, key, value):
        self.__root[key] = value

    def __iter__(self):
        return PropIterator(PickleTree(self.__root))

    def iteritems(self):
        return self.__root.iteritems()

    def __str__(self):
        txt = ""
        for elem in self:
            txt += str(elem)
        return txt

    def has_key(self,key):
        return self.__root.has_key(key)



def Retrieves(cls, property, modifier=None, isPicklableObject=False):

    # This descriptor incrementally builds a tree of properties
    # (PickleTree)
    #
    #          / size (fn, modif)
    #     ____/
    #    /    \
    #   /file  \ name (fn, modif)
    #  .
    #   \
    #    title (fn, modif)
    #
    # nested properties (like 'file.size') are supported.
    # This is particularly useful for formats like JSON.
    #

    def factory(method):
        if type(cls) == str:
            clsList = [cls]
        else:
            clsList = cls

        for clazz in clsList:
            if not globalPickleMap.has_key(clazz):
                globalPickleMap[clazz] = PickleTree({})

            setProp(globalPickleMap[clazz],
                    property.split('.'),
                    method,
                    modifier,
                    isPicklableObject)

        return method

    return factory

def Updates(cls, property, modifier=None):

    #Similar to @Retrieves

    def factory(method):
        if type(cls) == str:
            clsList = [cls]
        else:
            clsList = cls
        for clazz in clsList:
            if not globalUnpickleMap.has_key(clazz):
                globalUnpickleMap[clazz] = PickleTree({})
            setProp(globalUnpickleMap[clazz], property.split('.'), method, modifier)

        return method

    return factory

class DictPickler:

    @classmethod
    def pickle(cls, object, timezone = None):
        """ timezone can be a string (preferred) or a pytz.timezone object
        """

        # path mapping supported
        # i.e. getFileSize() ==> file.size

        if object is None:
            return None
        elif type(object) == list or type(object) == tuple or type(object) == set or isinstance(object, PersistentList):
            res = []
            for obj in object:
                res.append(DictPickler.pickle(obj, timezone))
            return res
        elif type(object) == dict or isinstance(object, PersistentMapping):
            res = {}
            for key, obj in object.iteritems():
                if not isinstance(key, basestring):
                    raise Exception("Key %s cannot be pickled because it's not a string. object=%s" % (str(key), str(object)))
                res[key] = DictPickler.pickle(obj, timezone)
            return res
        elif isinstance(object, basestring):
            return object
        else:
            clazz = classPath(object.__class__)
            if not globalPickleMap.has_key(clazz):
                raise Exception('Class %s is not supposed to be pickled. object=%s' % (clazz, str(object)))

            return DictPickler._pickle(object, globalPickleMap[clazz], timezone)

    @classmethod
    def update(cls, object, dict):

        # path mapping supported
        # i.e. file.size ==> setFileSize()

        clazz = classPath(object.__class__)
        if not globalUnpickleMap.has_key(clazz):
            raise Exception('Class %s is not supposed to be pickled. object=%s' % (clazz, str(object)))

        return DictPickler._update(object, globalUnpickleMap[clazz], dict)

    @classmethod
    def _update(cls,object,unpickleTree,dict):

        def recursiveUpdate(dict, prop):

            for (key,elem) in dict.iteritems():
                nextPath = functional_append(prop, key)
                if type(elem) == 'dict':
                    recursiveUpdate(object, elem, nextPath)
                else:
                    for (eprop, (method, modifier,isObj)) in unpickleTree:
                        if eprop == nextPath:
                            if (modifier):
                                method(object,modifier(elem))
                            else:
                                method(object,elem)


        recursiveUpdate(dict, [])

    @classmethod
    def _pickle(cls,object,pickleTree, timezone):

        def recursiveAttribution(obj, prop, result):
            if len(prop) == 1:
                obj[prop[0]] = result
            else:
                if not obj.has_key(prop[0]):
                    obj[prop[0]] = {}
                recursiveAttribution(obj[prop[0]], prop[1:], result)

        resDic = {}

        for (prop, (method, modifier, isObj)) in pickleTree:
            if method == None:
                result = object
            else:
                result = method(object)

            # apply the modifier, if there is one
            if (modifier):

                if modifier == Conversion.datetime:
                    result = modifier(result, tz = timezone)
                else:
                    result = modifier(result)

            if isObj:
                result = DictPickler.pickle(result)

            recursiveAttribution(resDic, prop, result)

        return resDic
