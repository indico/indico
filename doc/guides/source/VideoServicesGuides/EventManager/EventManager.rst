============
Introduction
============

Indico allows event managers to book and program remote collaboration sessions
(videoconferences, webcasts, etc.) and recording requests associated with their
events. Other Indico users can see information about these videoconferences in
the public pages of the events.

Event managers can now also perform service requests by filling out
forms that now appear inside Indico's event management interface.
Examples of such requests are the *Recording Request* and the
*Webcast Request*.

Three different kinds of Indico users can make use of this
functionality:

- The creator of an event.

- An event manager appointed by the creator of the event (or another
  manager).

- A Video Services manager, appointed by the event creator or one of
  the event managers. These users have privileges to access the
  *Video Services* section but cannot access any other section in
  the event management interface.

After an event is created, the management interface of an Indico
event is similar to figure 1:

|figure01|

Figure 1. Management interface for an Indico event, currently in
the *General Settings* section.
The *Video Services* section is highlighted in orange.

Your event should have a *Video Services* section (marked in
orange), unless the Indico administrators have deactivated all the Video Services systems for your kind of event (Lecture, Meeting, or Conference) or for all kinds of event.

==========================
The Video Services section
==========================

Click on the *Video Services* link to access the *Video Services*
section.

*Note* : the page that will be loaded now will possibly be HTTPs
(the URL in the browser should start by https:// ... ).

In the *Video Services* section, you will see something similar to
this:

|figure02|

Figure 2. *Video Services* section for an event. The
*Videoconferencing* tab is selected.

You should see several tabs. Only tabs corresponding to systems
enabled for your kind of event (Lecture, Meeting, Conference) will appear. In the above image, the tabs are *Videoconferencing*, *Recording* *Request* , *Webcast* *Request* and *Managers* .

The *Managers* tab is always present and lets you appoint other
people so that they have rights to manage part of, or all of, the
*Video Services* section. We will talk about the *Managers* tab
later.

The other tabs group the different Video Services systems. At the time this guide was written, there are five such systems: EVO, CERNMCU and Vidyo (all of them Video Conference systems grouped under the *Videoconferencing* tab), Recording Request and Webcast Request.

===========================
Video Services system types
===========================

There are two types of system: *booking* systems and *request*
systems.

*Booking* systems let you book resources in videoconferencing
systems, such as virtual meeting room in EVO (Enabling Virtual Organizations) or a videoconference in CERN's MCU.

*Request* systems let you request services for your event, such as
requesting that your event be recorded ( *Recording Request)* or
webcasted ( *Webcast Request)* .

---------------
Booking systems
---------------

EVO, CERNMCU and Vidyo are *booking* systems. They let you make a videoconference booking in EVO, Vidyo or CERN's MCU associated with your event. You can make more than one booking of each type for your Indico Event.

This chapter of the guide discusses common functions of these
systems. For more details about how to manage booking for the EVO
system in particular, see chapter `EVO system <#the-evo-system>`_.
For more details about CERNMCU bookings, please see chapter `CERNMCU system <#the-cernmcu-system>`_
For more details about how to manage booking for the Vidyo system see chapter `Vidyo system <#the-vidyo-system>`_

~~~~~~~~~~~~~~~~~~
Creating a booking
~~~~~~~~~~~~~~~~~~

To create a booking, select a system (EVO, CERNMCU or Vidyo) and click
*Create* .

|figure03|

Figure 3. Creating an EVO booking.

A pop-up dialogue will appear, asking you for data. This pop-up has two tabs: *Basic* and *Advanced* . The *Basic* tab contains the basic, important data that you need to fill in in order to make a
booking.

|figure04|

Figure 4. Dialogue to create an EVO booking. Basic tab.

The content under the Advanced tab contains more details you may
want to configure about your booking.

|figure05|

Figure 5. Advanced tab to create a booking.

After you have filled in the fields, press the *Save* button. If
there is a mistake with any of the fields, they will be highlighted in red. For example, in figure 6 below, there are two problems: the description is empty and the end date of the booking is before the start date (which is unreasonable).

If there were no mistakes, please wait until the booking is created
in the EVO system or the CERNMCU system.

~~~~~~~~~~~~~~~~
List of bookings
~~~~~~~~~~~~~~~~

After you have created the booking, it will appear under
*Current Bookings* . In figure 7 below, two bookings have already
been created. As you can see, the most recently created or
modified booking is highlighted in yellow for some seconds.

|figure07|

Figure 7. List of already created bookings.

When bookings have been created, they are organized as rows of a
table / list.

- The *Type* column specifies the type of booking (EVO, CERNMCU or Vidyo).

- The *Status* column specifies the current status of the booking. If
  you want to reload or update the status, press the |image0| button
  (*reload)* . This will query the remote system (EVO, CERNMCU or Vidyo) to
  see if there have been any changes. For example, maybe it is
  already time to start the booking; or maybe an administrator of EVO,
  CERNMCU or Vidyo has deleted your booking for some reason.

- The *Info* column gives a short summary of relevant information
  about this booking. This depends on the kind of booking involved.

- Between *Info* and *Actions,* you will find the |image1| button
  (*edit* ) and the |image2| button (*delete* ).

  + If you press the edit button, the same pop-up dialogue as when you
    created the booking will appear, and you will be able to modify the
    data.

  + If you press the delete button, after a confirmation warning, you
    will be able to delete the booking (both from Indico and from the
    remote system transparently).

    |figure08|

    Figure 8. Confirmation dialogue for removing a booking .

  + It is possible that the delete button is disabled: |image3|. This
    means you cannot delete the booking at the moment. For example, the
    EVO system does not allow you to delete bookings which have already taken
    place.

- In the *Actions* column, you can trigger some commands related to
  your booking.

  + If you press the *Start* button, the videoconference will start.

  + The Stop button will stop it.

  + If they are disabled (greyed out), you cannot perform this action
    at the moment.

- Please notice the |image6| button on the left of each row. If you
  press it, you will get detailed information about the booking.

  Figure 9. List of already created bookings, showing details of the
  first booking .

Finally, please note that the current timezone of the times that
appear on this page is shown to you on the top right corner, as a
reminder. It is the same timezone as the one you set up for the
event in the *General Settings* section.

|figure10|

Figure 10. Timezone reminder.

~~~~~~~~~~~~~
Event display
~~~~~~~~~~~~~

After you have created the bookings, they will appear on the event
display page, as shown in figure 11 below:

If you do not want your booking(s) to be publicly visible, check
the *Keep this booking hidden* checkbox in the Advanced tab of the
creation and modification pop-up dialogues.

For details about how bookings are displayed in the Event display
page, please consult the
`How to join a video service <../UserGuide/index.html>`_ document.


================================
Details about individual systems
================================

----------------
The Vidyo system
----------------

Vidyo videoconferencing system is a pioneer in a new era of videoconferencing products that deliver HD quality over the Internet. The system leverages the new H.264 Scalable Video Coding (SVC) standard, results in the industry's best resilience and lowest latency to be accomplished over converged IP networks. Vidyo can be used from a variety of platforms ranging from Mac & Windows desktops to dedicated H.323 devices and phone accesses.

~~~~~~~~~~~~~~~~~~~~~~~~
Creating a Vidyo booking
~~~~~~~~~~~~~~~~~~~~~~~~

To create a Vidyo booking, select *Vidyo* in the list of systems and
then click on *Create*. Vidyo has a different concept than EVO. In EVO you need to make a booking everytime you need a videoconference for a given event. In Vidyo, the booking needs to be done only once, provided that this room is used regularly. If the room is not used anymore, the system will automatic cleanup the room.

|figure54|

Figure 54. Creating a *Vidyo* booking.

The Vidyo creation pop-up dialogue will appear:

|figure55|

Figure 55. Vidyo booking creation dialogue.

In the *Basic* tab, you should fill in the following fields:

- *Room name* : this is the name the room in Vidyo will have

- *Description* : this is the description of room

- *Event linking* : one can link a vidyo booking to the event (default), a session or a contribution. The event can be linked to several vidyo rooms, however the sessions and contributions can be linked only to one vidyo room

- *Moderator* : The moderator will be the room responsible and will own the rights to moderate the vidyo room

- *Moderator PIN* : this is the code to grant moderator rights

- *Meeting PIN* : this is the code to protect the room

- *Automute* : enabling automute forces that the VidyoDesktop clients will join the meeting muted by default (audio and video)

In the *Advanced tab*, there are three options:

- *Display the Public room's PIN* : if one wants the PIN to be published on the event page, one should tick this option

- *Display auto-join URL in event page* : this is the URL that you can give to other people so that they can join the meeting. Just paste it into a browser and the Vidyo client will be launched. After authentication, the client will automatically join the meeting, prompting the user for a PIN if an access PIN was set up

- *Keep this booking hidden* : by default this option is not enabled.
  If you activate it, your booking will not appear on the public
  display page of your event.

  |figure56|

  Figure 56. Advanced tab for an Vidyo booking.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After creating a Vidyo booking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once your booking has been created, it will appear under the
*Current Bookings* List.

|figure57|

Figure 57. List of current bookings after a Vidyo booking was
created.

From left to right:

1. You can press the |image11| button to see the detailed
information of your booking:

|figure58|

Figure 58. Details of a Vidyo booking.

The details given are:

- *Room name* :this is the name of the room

- *Extension* : this is the numeric extension of the room, that gives another possibility of joining it. If one is logged in the Vidyo portal, one can join a room by entering the extension in the field "Select from list or Enter name to call"

- *Room moderator* : this is the owner of the room, which has moderation rights

- *Moderator PIN* : this is the code to grant moderator rights

- *Meeting PIN* : this is the code to protect the room

- *Description*: this is the description of the room

- *Auto-join URL* : this is the URL that you can give to other people
  so that they can join the meeting. Just paste it into a browser and
  the Vidyo client will be launched. After authentication, the client
  will automatically join the meeting, prompting the user for a
  PIN if an access PIN was set up.

- *Visibility* :  if visible, your booking will appear on the public display page of your event

- *Automute* : enabling automute forces that the VidyoDesktop clients will join the meeting muted by default (audio and video)

- *Created on* : this shows when the booking was created.

- *Last modified on* : this shows the last time that the
  booking information was modified.

- *Linked to* : this is the link of the vidyo room: it can be the event, a session or a contribution.

Also, in case of problems, there will be information in red in the
details. More on that in section
`Problems when creating or modifying Vidyo bookings <#problems-when-creating-or-modifying-a-vidyo-booking>`_

2. *Vidyo* refers to the type of this booking.

3. *Status* This is a substantial difference between Vidyo and EVO: In Vidyo you don't need to create a booking every time you need  for your event. The system is reservationless, so you create it only once and it stays valid. Therefore the only *Status* is *Public room created*. In addition the system has a configurable mechanism to remove old rooms. Old rooms are the ones that have absolutely no activity during a long period of time (currently set to 1 month). If this occurs you will be notified.

4. *Info* : this gives you info about the room extension

5. |image14| button (*edit* ). Press this button to change the data
of the booking, in case you need to perform a correction or a
change. Your changes will change the booking in Vidyo too.

6. |image15| button (*remove* ). Press this to delete your booking.
You will be asked for confirmation.

7. |figure80| button (*start desktop* ). Press this button
to launch the Vidyo client and have your PC join the videoconference
automatically.

8. |figure81| button (*connect room* ). Press this button
to launch the Vidyo client in the conferences/session/contribution physical room. In order to have this button enabled the room has to be a capable Vidyo room.

9. |figure82| button (*disconnect room* ). Press this button
to stop the Vidyo client in the conferences/session/contribution physical room. In order to have this button enabled the room has to be a capable Vidyo room.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Problems when creating or modifying a Vidyo booking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the booking creation and modification dialogue, it is possible
that when you try to save your booking, some of the fields are
highlighted in red.

|figure59|

Figure 59. In the *Vidyo booking creation* dialogue, some fields were highlighted in red in order to point out mistakes.

Situations where this can happen:

- *You left the room name empty* . The *Room name* field will be
  highlighted in red.

- *You left the meeting description empty* . The *Description* field
  will be highlighted in red.

- *You choose a link type that does not have items*. The "Linked to" select field will be highlighted in red.

Problems when you come to the Collaboration tab or when you
update the status:

- Room no longer exists: the room was too old (no activity has been detected for a certain period of time). The system autocleans it. You can at any time create a new one.
- *The booking has been deleted by Vidyo* . It is possible that the administrators of the Vidyo system have deleted your booking for some reason. Indico checks this and informs you if it is the case. This occurrence should be very rare.

- *The booking's data has been changed by Vidyo* . It is possible that
  the administrators of the Vidyo system have modified your booking for
  some reason (maybe the title was inappropriate, or a similar
  reason). Indico checks for this and informs you if it is the case,
  listing the changed fields.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Search option for Vidyo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The user has also the option to search for Vidyo rooms that either belong to him or to
events that he is manager of.

|figure83|

~~~~~~~~~~~~~~~~~~
Event display page
~~~~~~~~~~~~~~~~~~

You can see the full details of this section in the `How to join a video service
guide <../UserGuide/VideoServicesUserGuide.html#the-vidyo-system>`_.



~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Starting a Vidyo videoconference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can see the full details of this section in the `How to join a video service
guide <../UserGuide/VideoServicesUserGuide.html#the-vidyo-system>`_.


==============================
Requesting webcast & recording
==============================

The Webcast/Recording plugin enables webcast and recording services in Indico.


--------------------
Submitting a request
--------------------

Webcast and recording requests can be handled in the
`Event Services menu <../../UserGuide/EventServices.html>`_


---------------------
Result of the request
---------------------

For the recordings, once the request is accepted, the event manager will need to
send to every speaker that will be recorded an email asking to sign the speaker
release form. This will be done through the
`Event Agreements menu <../../UserGuide/EventAgreements.html>`_.


.. |image0| image:: images/html_4108b437.png
.. |image1| image:: images/html_m7f295075.png
.. |image2| image:: images/html_25c4d730.png
.. |image3| image:: images/html_m1976455e.png
.. |image6| image:: images/html_m640d2242.png
.. |image11| image:: images/html_m640d2242.png
.. |image14| image:: images/html_m7f295075.png
.. |image15| image:: images/html_25c4d730.png
.. |figure01| image:: images/html_66602418.png
.. |figure02| image:: images/html_7b1f9bab.png
.. |figure03| image:: images/fig3.png
.. |figure04| image:: images/html_m1ce614f6.png
.. |figure05| image:: images/html_m31e3c44.png
.. |figure07| image:: images/html_2c7ef69.png
.. |figure08| image:: images/html_5abfb4ff.png
.. |figure10| image:: images/html_502b89e9.png
.. |figure54| image:: images/fig54.png
.. |figure55| image:: images/fig55.png
.. |figure56| image:: images/fig56.png
.. |figure57| image:: images/fig57.png
.. |figure58| image:: images/fig58.png
.. |figure59| image:: images/fig59.png
.. |figure76| image:: images/fig76.png
.. |figure80| image:: images/fig80.png
.. |figure81| image:: images/fig81.png
.. |figure82| image:: images/fig82.png
.. |figure83| image:: images/search_vidyo.png
