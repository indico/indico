# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


class classproperty(property):
    def __get__(self, obj, type=None):
        return self.fget.__get__(None, type)()


class strict_classproperty(classproperty):
    """A classproperty that does not work on instances.

    This is useful for properties which would be confusing when
    accessed through an instance.  However, using this property
    still won't allow you to set the attribute on the instance
    itself, so it's really just to stop people from accessing
    the property in an inappropriate way.
    """
    def __get__(self, obj, type=None):
        if obj is not None:
            raise AttributeError('Attribute is not available on instances of {}'.format(type.__name__))
        return super(strict_classproperty, self).__get__(obj, type)


class cached_classproperty(property):
    def __get__(self, obj, objtype=None):
        # The property name is the function's name
        name = self.fget.__get__(True).__func__.__name__
        # In case of inheritance the attribute might be defined in a superclass
        for mrotype in objtype.__mro__:
            try:
                value = object.__getattribute__(mrotype, name)
            except AttributeError:
                pass
            else:
                break
        else:
            raise AttributeError(name)
        # We we have a cached_classproperty, the value has not been resolved yet
        if isinstance(value, cached_classproperty):
            value = self.fget.__get__(None, objtype)()
            setattr(objtype, name, value)
        return value


def cached_writable_property(cache_attr, cache_on_set=True):
    class _cached_writable_property(property):
        def __get__(self, obj, objtype=None):
            if obj is not None and self.fget and hasattr(obj, cache_attr):
                return getattr(obj, cache_attr)
            value = property.__get__(self, obj, objtype)
            setattr(obj, cache_attr, value)
            return value

        def __set__(self, obj, value):
            property.__set__(self, obj, value)
            if cache_on_set:
                setattr(obj, cache_attr, value)
            else:
                try:
                    delattr(obj, cache_attr)
                except AttributeError:
                    pass

        def __delete__(self, obj):
            property.__delete__(self, obj)
            try:
                delattr(obj, cache_attr)
            except AttributeError:
                pass

    return _cached_writable_property
