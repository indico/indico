.. _protection_guide:

=================
Protection System
=================

Introduction
------------

This section aims to describe the protection system used by
Indico to grant or restrict access to users.

--------------

Basic Concepts
--------------

Inheritance Graphic
~~~~~~~~~~~~~~~~~~~

You can set up a protection policy for almost all the objects that
you can create within Indico. This protection policy is based on an
inheritance system, meaning that an object is going to inherit the
protection from its father, e.g., a contribution can be public but
becomes private if we set up its container (a meeting) as private.

The protection objects tree is as shown in the following picture:

|image208|

As we can see, a **File** inherits the protection policy from
*Material*, *Material* from *Contribution*, *Contribution* from
*Session*, *Session* from *Event*, *Event* from *Sub-category* and
*Sub-category* from *Category.*
The next picture shows an example of this inheritance system.
"Category A" is RESTRICTED and because of this, "Conference 1" becomes
RESTRICTED too. As User 1 and User 2 are in the access list for
"Category A" they can also access "Conference 1". The rest of Indico
users cannot access "Category A" and "Conference 1".

|image209|

--------------

Protection Types
~~~~~~~~~~~~~~~~

For each object (category, conference, contribution, session,
etc) in Indico, one can set up three kinds of protection:
modification control list, access control setup, and domain control.

-
   The modification control list contains all the users or groups that can
   edit and modify an object. Therefore, people in this list will be
   the managers for the object and they can access all the pages
   related to it and the objects under it.
-
   Access control setup: by default, an object is inheriting but we can
   make it public or private and add restrictions as shown in the section
   `Access Control Policy <#id1>`_.
-
   Domain control: one can protect an Indico object to be accessed
   only by users who are connected from some given IPs (see
   `Domain Control Policy <#id3>`_).


--------------


.. _access_control:

Access Control Policy
---------------------


In Indico, an object can be a category, an event, a session, a contribution,
material, files and links. You need to assign a level of protection to
all of these events. There are three different kinds of events in Indico:


**Public**: Making an object public will make it accessible and visible
to anyone. For example, suppose conference A belongs to category A. If
the category A is private, but the conference A is public, then only
allowed users will be able to access the category A, but everyone can
access conference A.

|image210|

In this graph, only restricted users have access to Category A, but
everyone can access Conference A, as it is public.


**Restricted**: Making an object private will make it invisible to all
users. You will then need to set the users which will have access to it.
For example, suppose category B is public and conference B is private,
and you allow users 1 and 2 to access the conference. Then everyone will
have access to category B, but only users 1 and 2 will be able to see
conference B.

|image212|

In this graph, everyone can access Category B, but only restricted users
can access Conference B, as it has been made private.


**Inheriting**: Making an object inheriting makes it inherit the access
protection of its parent. Changing the protection of the parent will
change the protection of the object. For example, suppose conference C
belongs to category C. If you make category C private, then conference C
will be private; if category C is public, then conference C will be public.
Making a category which belongs to the category *Home* inheriting
will make the category public by default.

Here is a graph that illustrates the inheriting example.


   |image211|

In this graph, we see how Category C transmets its access protection to
Conference C (which is included in it), i.e. how Conference C inherits
its access protection from its parent category, Category C.

By default, all objects in Indico are INHERITING.


--------------

Domain Control Policy
---------------------

If an Indico object (category, event, session, contribution,
material, file and link) is PUBLIC, we can restrict the access to
users accessing Indico from some given IPs (these IPs could be like
127.1 which means that every IP starting like this will be valid).

If the Indico object is RESTRICTED, this checking will not be
applied.

If it is INHERITING, it will have the same access protection as its
parent. Its access protection status will therefore change whenever
the parent's access protection changes.

.. |image208| image:: UserGuidePics/tree.png
.. |image209| image:: UserGuidePics/privByInh.png
.. |image210| image:: UserGuidePics/privatePublic.png
.. |image211| image:: UserGuidePics/inheriting.png
.. |image212| image:: UserGuidePics/publicPrivate.png
