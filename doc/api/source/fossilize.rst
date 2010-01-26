:mod:`fossilize` -- "Serializing" elaborate Python objects to dictionaries and lists
====================================================================================

.. automodule:: MaKaC.common.fossilize
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

        def getFriends(self):
            """ His/her friends """
        getFriends.result = ISimpleUserFossil

Output::

    >>> u1 = User(1,'john')

    >>> u1.fossilize(ISimpleUserFossil)
    {'id': 1, 'name': 'JOHN'}

    >>> u2 = User(2,'bob')

    >>> u3 = User(3, 'lisa', friends=[u1,u2])

    >>> u3.fossilize(IComplexUserFossil)
    {'friends': [{'id': 1, 'name': 'JOHN'}, {'id': 2, 'name': 'BOB'}], 'id': 3}

    >>> fossilize([u1, u2, u3], ISimpleUserFossil)
    [{'id': 1, 'name': 'JOHN'},
     {'id': 2, 'name': 'BOB'},
     {'id': 3, 'name': 'LISA'}]

