.. _indico_glossary:

Indico's Glossary
=================

.. glossary::
   :sorted:

   Absolutely Public
     The state in which a resource is public, regardless of the status
     that is inherited from the parent resource.

   Abstract
     Ideas or summary of a presentation/contribution, often assigned to
     a track. Once accepted becomes a contribution.

   Account
     A register, associated with a user, and that enables him/her to
     authenticate his/her identity. Indico supports local accounts, LDAP
     and SSO.

   Avatar
     An "Avatar" is a representation of a user in the Indico database.
     It usually contains all the user's personal info.
     These data can be explicitly modified by the user. An Avatar is
     normally associated with one or more accounts.

   Break
     A pause in the schedule of a meeting/conference. Breaks can be
     placed inside sessions/slots or at the top level.

   Category
     A container for events. Categories can contain either other
     categories (sub-categories), or events, never both at the same
     time. The category hierarchy of Indico resembles a tree where
     categories that contain events are the "leaves".

   Clone
     Cloning a meeting means replicating it (with the exact same
     information) on a diferent date. This is normally useful for series
     of meetings whose participans and/or contents don't change
     significantly.

   Conference
     The most complex kind of event, containing the same as a meeting,
     plus support for registration, abstract management, and other
     features that are specific to this kind of event.

   Contribution
     Usually a presentation taking place within a session or slot.

   Evaluation
     A poll, that is conducted normally after an event takes place, so
     that the organizer can gather feedback about it. It can be applied
     to any event, and the results can be exported as stylesheets.

   Event
     An event is either a Lecture, Meeting or Conference.

   File
     In the context of Indico, this is a resource that links to a
     physical file, contained in Indico's "archive". Files are stored
     inside materials.

   Lecture
     A presentation, normally done by one or more speakers. It doesn't
     contain any "substructures" such as contributions.

   Link
     In the context of Indico, a Link is a resource that links to some
     other resource on the Web, specified by a URL. Links exist inside
     materials.

   Material
     A Material is a container for Files and Links, it groups resources
     of the same nature (i.e. slides, documents, drawings...). Materials
     can be attached to Categories (quite rare), Events, Sessions,
     Contributions and Subcontributions.

   Meeting
     A kind of event that implies some degree of participation from
     different participants, over different topics (Contributions).
     Contributions can be placed into Sessions, for better organization.
     Slots can also be used, but they are disabled by default.

   Minutes
     Minutes are annotations produced by participans in a meeting. They
     can be associated with Meetings, Sessions, Contributions and
     Subcontributions.

   Restricted
     A status in which a resource cannot be accessed by users that do
     not accomplish certain criteria (i.e. being in a list, or coming
     from a specific IP domain...).

   Restricted by Inheritance
     A status in which an resource is private just because its parent
     resource was set as private (either by inheritance, or
     explicitly).

   Public
     A status in which a resource is publicly accessible, with no
     constraints. This status can be overriden, if the parent resource
     is set as private (see Restricted by Inheritance).

   Resource
     In the context of this document, a Resource is a category, event
     (lecture, meeting or conference), session, contribution,
     subcontribution, material, link or file. It is basically any
     information-bearing object in Indico's domain.

   Session
     A time slot to help organise your conference timetable. Can contain
     slots, contributions and breaks.

   Slot
     A session can be split into slots, can be used when the session
     happens over more than one period of time. Can contain
     contributions and breaks.

   Subcontribution
     A subdivision of a contribution.

   Track
     Tracks define the main divisions/topics of your conference. You can
     attach contributions and abstracts to tracks.

   Visibility
     In the context of Indico, Visibility usually refers to the extent
     to which an event can be seen in the event overview page. This
     attribute sets whether the event can be seen as belonging to the
     top level class (and all those below), to none of them (invisible),
     or to one of the intermediate classes (and all those below).

