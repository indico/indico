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

from MaKaC.common.contextManager import ContextManager

class ExternalOperationsManager(object):
    """ Acts as a wrapper / proxy for ContentManager in order to store if remote operations
        performed by plugins (such as creating a booking in a remote system, or sending a mail)
        are not executed more than once in case of a DB ConflictError.

        VERY IMPORTANT: when wrapping an operation with execute() or manually using storeResult and getResult,
        the function you are wrapping should not modify anything in the DB, just do the external action.
        This is because in case of ConflictError, the DB will return to its initial state but the
        function will not be executed again, so eventual modifications to the DB done by the function will be lost.

        The "obj" and "operation" parameters are used to decide the key used in the "storage" for storing
        the operation result (which will be None if the operation does not return anything).
        If the "obj" has a getUniqueId() method, it will be used. This method is already defined for many classes, but...
        WARNING: some of the classes that define getUniqueId() just return the unique id of their parent object.
        If you must use an instance of that class as obj, consider changing the code of that class's getUniqueId() method,
        pass a string instead of an object, or change how the ExternalOperationsManager._objectToKey() method works.
    """

    @classmethod
    def execute(cls, obj, operation, function, *args, **kwargs):
        """ If the operation gets executed for the first time on the object,
            the function gets executed with the arguments and the result is stored and returned.
            If it's not the first time, the function is not executed and the previous result is returned.
        """
        try:
            return cls._getResult(obj, operation)
        except KeyError:
            result = function(*args, **kwargs)
            return cls._storeResult(obj, operation, result)

    @classmethod
    def _storeResult(cls, obj, operation, result):
        """ Stores a result based on an operation and the object it is applied to.
            The storage is a dictionary of 2 levels:
            {_objectToKey(obj): {operation: result}}
            The obj is translated into a key with the _objectToKey function.
        """
        storage = cls._getStorage()
        key = cls._objectToKey(obj)
        storage.setdefault(key, {})[operation] = result
        return result

    @classmethod
    def _getResult(cls, obj, operation):
        """ Throws KeyError if we had not stored results for this object
            or for this operation on this object
        """
        storage = cls._getStorage()
        key = cls._objectToKey(obj)
        return storage[key][operation]

    @classmethod
    def _getStorage(cls):
        """ Returns the dictionary where the results are stored.
            The dictionary is stored inside the ContentManager
        """
        return ContextManager.setdefault("collaborationRemoteOperations", {})

    @classmethod
    def _objectToKey(cls, obj):
        """ We cannot simply use the object as key because sometimes the object
            that is key is constructed (by calling its class's constructor) for every ConflictError retry,
            in which case it is NOT the same object every time.
        """
        if hasattr(obj, "getUniqueId"):
            return obj.getUniqueId()
        else:
            return obj

