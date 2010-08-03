:mod:`indico.util.fossilize` -- "Serializing" elaborate Python objects to dictionaries and lists
================================================================================================

.. automodule:: indico.util.fossilize
   :members:

=======
Example
=======

A simple example class::

    class User(Fossilizable):

        fossilizes(ISimpleUserFossil, IComplexUserFossil)

        def __init__(self, id, name, friends = []):
            self.id = id
            self.name = name
            self.friends = friends

        def getId(self):
            return self.id

        def getName(self):
            return self.name

        def getFriends(self):
            return self.friends

(note that the code above will fail if the fossils below are not declared first)

A simple example `Fossil`::

    class ISimpleUserFossil(IFossil):
        """ A simple user fossil """

        def getId(self):
            """ The ID of the user """

        def getName(self):
            """ The name, in uppercase """
        getName.convert = lambda x: x.upper()

A slightly more complex `Fossil`::

    class IComplexUserFossil(IFossil):
        """ A complex user fossil """

        def getId(self):
            """ The ID of the user """
        getId.name = 'identityNumber'

        def getFriends(self):
            """ His/her friends """
        getFriends.result = ISimpleUserFossil

Output::

    >>> u1 = User(1,'john')

    >>> u1.fossilize(ISimpleUserFossil)
    {'id': 1, 'name': 'JOHN', '_type': 'User', '_fossil': 'simpleUserFossil'}

    >>> u2 = User(2,'bob')

    >>> u3 = User(3, 'lisa', friends=[u1,u2])

    >>> u3.fossilize(IComplexUserFossil)
    {'friends': [{'identityNumber': 1, 'name': 'JOHN', '_type': 'User', '_fossil': 'simpleUserFossil'},
                 {'id': 2, 'name': 'BOB', '_type': 'User', '_fossil': 'simpleUserFossil'}],
                 'id': 3, '_type': 'User', '_fossil': 'complexUserFossil'}

    >>> fossilize([u1, u2, u3], ISimpleUserFossil)
    [{'id': 1, 'name': 'JOHN', '_type': 'User', '_fossil': 'simpleUserFossil'},
     {'id': 2, 'name': 'BOB', '_type': 'User', '_fossil': 'simpleUserFossil'},
     {'id': 3, 'name': 'LISA', '_type': 'User', '_fossil': 'simpleUserFossil'}]

===============
Advanced topics
===============

Valid fossil names. Fossil base class
-------------------------------------

Valid fossil names have to start with ``I`` (from "interface") and finish with ``Fossil``, i.e. they have to comply with the regular expression:: ``^I(\w+)Fossil$`` .

Also, fossils have to always inherit directly or indirectly from the ``IFossil`` fossil,
which in turns inherits from ``zope.interface.Interface``.


_type and _fossil
-----------------

All of the fossilized objects produced will have a ``_type`` attribute, with the name of the original object's class,
and a ``_fossil`` attribute with the name of the fossil used:

    >>> u = User(1, 'john')
    >>> u.fossilize(u, ISimpleUserFossil)
    {'id': 1, 'name': 'JOHN', '_type': 'User', '_fossil': 'simpleUserFossil'}

Valid method names
------------------

A fossil's method names have to be in the ``get*`` form, ``has*`` form, or ``is*`` form. Otherwise, the ``name`` tag is needed.
Example::

    class ISomeFossil(IFossil):
        """ A complex user fossil """

        def getName(self):
            """ The name of the user """

        def hasChildren(self):
            """ Returns if the user has chidlren or not """

        def isMarried(self):
            """ Returns if the user is married or not """

        def requiresAccomodation(self):
            """ Returns if the user requires accomodation or not """
        requiresAccomodation.name = 'requiresAcc'

Fossilizing an imaginary user object with this fossil would result in:

    >>> u.fossilize(ISomeFossil)
    { 'name': 'bob', 'hasChildren': False, 'isMarried': True, 'requiresAcc': True, '_type': 'User', '_fossil': 'someFossil'}

As shown, the ``getXyz`` methods correspond to a ``xwz`` attribute, the ``hasXwz`` methods correspond to a ``xwz`` attribute, and so on... The other methods need a ``name`` tag or an ``InvalidFossilException`` will be thrown.


Method tags
-----------

As seen in the example, it is possible to apply valued tags to the fossil methods:

    * ``name`` tag: overrides the normal name that would be given to the attribute by the fossilizing engine.

    * ``convert`` tag: applies a function to the result of the object's method. Useful to covert datetime objects into strings, capitalize strings, etc.

    * ``result`` tag: when the result of an object's method is another object that might be fossilized, you can specify which interface (fossil) to use with the ``result`` tag.


Different ways of specifying the fossil to use
----------------------------------------------

Let's take the User class from the first example, and an additional group class. We will not write their methods::

    class User(Fossilizable):
        """ Class for a User. A User has an id and a name """
        fossilizes(ISimpleUserFossil, IComplexUserFossil)

    class Group(Fossilizable):
        """ Class for a Group. A Group has an id and a groupName """
        fossilizes(ISimpleGroupFossil, IComplexGroupFossil)

The normal way to specify which fossil to use is to just write the fossil class:

    >>> u = User(1, 'john')
    >>> u.fossilize(u, ISimpleUserFossil)
    {'id': 1, 'name': 'JOHN', '_type': 'User', '_fossil': 'simpleUserFossil'}

This way should be used whenever we are sure that the object we are fossilizing is of a given class.

However, in some cases we are not sure of the interface that should be used. Or, we may be fossilizing a list of heteregenous objects and we cannot or we do not want to use the same fossil for all of them.

In this case, there are currently two options:

    * Use ``None`` as the interface (or leaving the interface argument empty). In this case, the "default" fossil will be used for each object, which means the first fossil declared with the ``fossilizes`` declaration in the object's class. If the object's class does not invoke ``fossilizes`` but one of its super-classes does, the first fossil from that super-class will be used. Example::

        >>> friends = [User(1, 'john'), Group(5, 'family')]
        >>> fossilize(friends)
        [{'id': 1, 'name': 'JOHN', '_type': 'User', '_fossil': 'simpleUserFossil'},
         {'id': 5, 'groupName': 'family', '_type': 'Group', '_fossil': 'simpleGroupFossil'}

    * Use a dictionary to specify which fossil should be used depending on the object's class. The keys of the dictionary can be: class objects, class names as strings, full class names as strings, or a class object corresponding to an object's super class. Examples::

        >>> friends = [User(1, 'john'), Group(5, 'family')]
        >>> fossilize(friends, {User: ISimpleUserFossil, Group: ISimpleGroupFossil})
        [{'id': 1, 'name': 'JOHN', '_type': 'User', '_fossil': 'simpleUserFossil'},
         {'id': 5, 'groupName': 'family', '_type': 'Group', '_fossil': 'simpleGroupFossil'}
        >>> fossilize(friends, {"User": ISimpleUserFossil, "Group": ISimpleGroupFossil})
        (same output)
        >>> fossilize(friends, {"package.subpackage.User": ISimpleUserFossil, "package.subpackage.Group": ISimpleGroupFossil})
        (same output)


Changing a fossil in execution time
-----------------------------------

If for some reason you need to change a fossil behaviour in execution time (i.e. after it has been imported),
know that it is possible, but **please, avoid doing this unless you have a very good reason for it**. All fossils inherit from zope.interface.Interface, which defines methods so that this is possible.

Example: change the 'name' tag of a given method of a fossil:

    >>> IComplexUserFossil.get('getFriends').setTaggedValue('name', 'myFriends')

