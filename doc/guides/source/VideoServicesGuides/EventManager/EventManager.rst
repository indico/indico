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

|figure11|

Figure 11. Event display page for a meeting, showing the bookings
previously made .

If you do not want your booking(s) to be publicly visible, check
the *Keep this booking hidden* checkbox in the Advanced tab of the
creation and modification pop-up dialogues.

For details about how bookings are displayed in the Event display
page, please consult the
`How to join a video service <../UserGuide/index.html>`_ document.

---------------
Request systems
---------------

*Recording Request* and *Webcast Request* are *request* systems.

Instead of performing a booking in a videoconference system, such
as EVO, CERN's MCU or Vidyo, these parts of the Video Services section are
useful to request a service for your event.

You can only perform one request of each type for your Indico
Event, although you can change its details after you send it.

Click on the *Recording Request* or *Webcast Request* tabs to
request these services. You will have to fill in a form for this
request.

By filling in these forms, you are requesting a CERN Recording
expert to come and record your event, or a CERN Webcast expert to
webcast your event.

These forms are very detailed and their purpose is to facilitate
the communication between you and the Recording or Webcast services.
Please take some time to fill them in correctly as that will save both
you and the services' responsibles valuable time.

We will discuss the details of the *Recording Request* form and the
*Webcast Request* form later, in chapters
`Recording Request system <#the-recording-request-system>`_ and
`Webcast Request system <#the-webcast-request-system>`_ The parts common
to both forms are found at their top and bottom: they are the
buttons to send, modify or withdraw the request.

|image7| |image8|

Figures 12 and 13 . Buttons to send / modify / withdraw a request.

Once the request has been submitted, a line will appear at the top
with the current status of the request, as shown in figure 14
below.

|figure14|

Figure 14. Status of a request.

The initial status will be *Request successfully sent* . This means
that an email has been sent to the corresponding responsible person
with all the details that you input in the form. After the service
responsible has decided if he accepts your request or not, he will
either accept or reject the request.

If the request is accepted, the status will look like this:

|figure15|

Figure 15. *Request accepted* status .

If the request has been rejected, the status will look like this:

|figure16|

Figure 16. *Request rejected* status, showing the rejection
reason.

You can see that in this case the responsible has also given you a
reason for his rejection.

In both cases (accept and reject), the following people will
receive an email as notification:

- The creator of the event.

- Any managers of the event.

- Any Video Services Managers (be it of all systems, or only of the
  corresponding one).

You can also come back to the page to see the status, or if you do
not want to reload the page, use the |image9| button to reload
(update) the status.

Even after a request is accepted or rejected, you can still modify
it, which will trigger another email to be sent to the responsible
person.

----------------
The Managers tab
----------------

The *Managers* tab lets you appoint other people to have rights to
access and use the Video Services section, even if these people are
not Event Managers themselves.

There are two types of Managers: *Video Services Managers* and
*Individual System Managers* .

|figure17|

Figure 17. *Managers* tab inside the *Video Services* section.

People added as *Video Services Managers* will be able to access
all the tabs of the Video Services section (Collaboration,
Recording Request, etc., and the Managers tab too) and perform any
operation that you can perform there.

In order to add someone, you can either click on *Add Indico User*
which will bring a standard user search pop-up dialogue, or click
*Add from favourites* which will bring up your favourite
users.

|figure18|

Figure 18. Adding a manager. We can add an existing user by
searching or by selecting one of our favourite ones.

Remember you can always change your favourite users by clicking on
your name at the top right corner and then going to *Favorites* .

|figure19|

Figure 19. Indico status bar. The user name is highlighted in
orange.
Click on it to go to your profile and then click on *Favorites* to
add or remove favourite users.

People added as a Manager for an individual system will see only
one of the tabs (the corresponding one for that system) and will be
able to manipulate only bookings or requests of that system.

As shown in figure 20 below, you can see how someone who is a Video
Services Manager views the management interface of an event:

|figure20|

Figure 20. View of the management interface by a manager. Only the
*Video Services* section is available.

And here how someone who is only a CERNMCU Manager views it:

|figure21|

Figure 21. View of the management interface by a CERNMCU manager.
Only the *Videconferencing* tab is available.

As you can see, even if the CERNMCU Manager can see the
Collaboration tab, he or she cannot see or create bookings of other
systems (EVO or Vidyo), unless of course he is also a manager of that other
system.

People added in the *Managers* tab can access the *Video Services*
section of an event by clicking on the |image10| icon
(*Modify Event* ).

In summary, you should add someone as Video Services Manager if you
want to give that person great control over the Video Services
section, including appointing other Video Service Managers; and add
people as individual system managers if you want to keep control
over what they can do.

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


----------------------------
The Recording Request system
----------------------------

The Recording Request system can be found under the
*Recording Request* tab.

The requester can only send one Recording Request for each Indico
Event, although after sending it, the details can still be
modified.

Every time a Recording Request is sent, modified or withdrawn, a
CERN's Recording Responsible will receive a notification email.

A **Recording Responsible** is a person who will go and physically
record your event, or a person who manages recording petitions.

After receiving the notification, the responsible will review the
request, and accept or reject it. The event creator will receive an
email notification.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Filling in a Recording Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To fill in a Recording Request, go to the *Recording Request* tab
in the *Video Services* section.

You will see a form that you have to fill in.

|figure60|

Figure 60. Top part of the *Recording Request* form.

From top to bottom, its elements are:

- A warning area that may or may not contain a warning message. In this
  screenshot, we get a warning because we have not chosen a
  Location in the General Settings page. Without a location, the
  Recording Responsible does not know where he or she has to go to
  record the event.

- A *Send Request* button. Press this to submit the request.

- A section concerning which talks are to be recorded. In Indico, a
  *talk* is defined as a contribution that is not inside a Poster
  session (therefore, not a poster).

  + First, you may select among three options:

    * To have all the talks of your event recorded.

    * To choose which ones you want recorded. If you choose this, a list
      of talks will appear below. It there are many talks to be
      displayed, you might experience a small delay while all the talks
      are loaded from the Indico server.

      |figure61|

      Figure 61. In this section of the form, you can select the talks
      (contributions) to be recorded.

      Select the contributions that you want to have recorded. Click on
      *Select All* or *Select none* to select or unselect all of the
      contributions.

    * If you cannot specify which talks you would like to have recorded
      with the *All Talks* or *Choose* options, then pick
      *Neither, see comment* , and write a comment in the line
      underneath.

  + Next, there is an area where you can write additional comments
    about the talk selection. These comments can complement your choice
    above or in case you chose *Neither, see comment* , they will
    specify the talks you want to have recorded.

  + Finally, you should specify if all the speakers have given
    permission to have their talks recorded. There is a link to a
    Recording Consent Form that each of the speakers should sign before
    being recorded.

    This sub-section is compulsory (you must choose *yes* or *no* ).

- The second section requests the following information:

  + Will slides and/or chalkboards be used? *This field is compulsory*.

  + What type of event is it? *This field is compulsory*.

  + How urgently do you need to have the recordings posted online?

  + How many people do you expect to view the online recordings
    afterwards? Please enter a number here.

  + How many people do you expect to attend the event in person? Please
    enter a number here.

- The third section requests the following information:

  + Why do you need this event recorded? Check all the check boxes that
    apply for your event.

  +  Who is the intended audience? Check all the check boxes that apply
     for your event.

  + What is the subject matter? Check all the check boxes that apply for
    your event.

- In the last section, you can add whatever comments you think are
  necessary.

- At the bottom of the form, there is another *Send Request* button
  for your convenience.

~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sending a Recording Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have filled in the form, click either *Send Request*
button to submit the request to the Recording Responsible.

|figure62|

Figure 62. *Send request* button.

Once the request has been submitted, a message will appear at the
top with the current status of the request.

|figure63|

Figure 63. After pressing *Send Request* , the status will change
to *Request successfully sent* .

The initial status will be *Request successfully sent* . This means
that an email has been sent to the Recording Responsible with all
the details that you input in the form.

Also, the *Send Request* buttons at the top and the bottom of the
form will disappear and will be replaced by *Modify Request* and
*Withdraw request* buttons.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Modifying a Recording Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After the request has been sent, you can still modify it. This is
useful if you noticed that you made a mistake or if the Recording
Responsible asks you to change some details of it.

Any time you return to the Recording Request page, information
entered previously will still be there, and you can always change
it and then press the *Modify Request* button to send the request
again.

This will reset the status to “Request successfully sent”, even if
the request had been accepted or rejected previously. The Recording
Responsible will receive a new mail with the request details.

|figure64|

Figure 64. *Modify request* and *Withdraw request* buttons.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Withdrawing a Recording Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can always withdraw a request if you consider it is no longer
necessary. The Recording Responsible will be notified by mail that
your request has been withdrawn.

After withdrawing a request, the Recording Request form will return
to its initial state; all the fields will be empty.

~~~~~~~~~~~~~~~~~~~~~
Result of the request
~~~~~~~~~~~~~~~~~~~~~

Once the request is sent, the Recording Responsible will either
accept or reject it.

If the request is accepted, the status will look as shown in figure
65 below:

|figure65|

Figure 65. *Request accepted* status.

If the request has been rejected, the status will look as shown in
figure 66 below:

|figure66|

Figure 66. *Request rejected* status. The rejection reason is
shown.

You can see that in this case the responsible has also given you a
reason for his rejection.

In both cases (accept and reject), you as the creator of the event
will receive an email notification.

You can also come back to the page to check on the status, or if
you don't want to reload the page, use the |image0| button to
reload / update the status.

Even after a request is accepted or rejected, you can still modify
it, which will trigger another mail being sent to the responsible.

*Note: Once the request is accepted, the manager will need to send to every
speaker that will be recorded an email asking to sign the speaker release form.
This will be done through the `Agreements menu <../../UserGuide/EventAgreements.html>`_.


--------------------------
The Webcast Request system
--------------------------

The Webcast Request system can be found under the *Webcast Request*
tab.

The requester can only send one Webcast Request for each Indico
Event, although after sending it, the details can still be
modified.

Every time that a Webcast Request is sent, modified or withdrawn, a
CERN's Webcast Responsible will receive a notification email.

A **Webcast** **Responsible** is a person who will be responsible
for webcasting your event, or a person who manages recording
petitions.

Then, the responsible will review the request, and accept or reject
it. The event creator will receive an email notification. If the
request is accepted, your event will be added to Indico's list of
events to be webcasted.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Filling in a Webcast Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To fill in a Webcast Request, go to the *Webcast Request* tab in
the Video Services section.

You will see a form that you have to fill in.

|figure67|

Figure 67. Top part of the *Webcast Request* form.

From top to bottom, its elements are:

- A warning area that may or may not contain warning messages. The
  warning messages may be:

  + A warning message to remind you that you need to book your room in
    Indico's Room Booking system.

  + You need to select a room capable of webcasting for your Indico
    event or at least one of your talks (a talk is a contribution
    within a session that is not a Poster session). Some rooms at CERN
    have the necessary equipment to webcast an event, and others do
    not.

    If you get this warning, you can click on
    *See list of webcast-able rooms* to see which rooms have been
    marked as webcast-able. This is how the warning looks:

    |figure68|

    Figure 68. Warning that will appear if neither your event
    nor any of your talks take place in a webcast-able room.

    Please note that if you get this warning, there is no point in
    making a Webcast Request until you select a webcast-able room. In
    this case, the rest of the form will be disabled and you will not
    be able to fill it in.

- A *Send Request* button. Press this to submit the request.

- A section concerning which talks you would like to have webcasted.
  In Indico, a *talk* is defined as a contribution that is not inside
  a Poster session (therefore, not a poster).

  + First, you may select among two options:

    * To have all the webcast-able talks of your event webcasted. A talk
      is webcast-able if it takes place in a room that has been marked as
      webcast-able.

      Here, you will be notified if some of your talks are not
      webcast-able. Such a situation is shown below:

      |figure69|

      Figure 69. Notification that will appear when some of your talks
      do not take place in webcast-able rooms.

    * The other option is to choose which talks you want webcasted. If
      you choose this, a list of talks will appear below. It there are
      many talks to be displayed, you might experience a small delay
      while all the talks are loaded from the Indico server.

      |figure70|

      Figure 70. Choosing among the list of webcast-able talks.

      Select the contributions that you want to have webcasted. Click on
      *Select All* or *Select none* to select or unselect all of the
      contributions.

  + Finally, there is an area where you can write additional comments
    about the talk selection. These comments can complement your choice
    about which talks should be webcasted.

- In the next section, you should specify if all the speakers have
  given permission to have their talks webcasted. This is a link to a
  Webcast Consent Form that each of the speakers should sign before
  being webcasted.

  This section is compulsory (you must choose 'yes' or 'no').

- The third section requests the following information:

  + Will slides and/or chalkboards be used? *This field is compulsory.*

  + What type of event is it? *This field is compulsory.*

  + How soon do you need your recording posted online afterwards?

  + How many people do you expect to view the online recordings
    afterwards? Please enter a number here.

  + How many people do you expect to attend the event in person? Please
    enter a number here.

- The fourth section requests the following information:

  + Why do you need this event webcasted? Check all the check boxes that
    apply for your event.

  + Who is the intended audience? Check all the check boxes that apply
    for your event.

  + What is the subject matter? Check all the check boxes that apply for
    your event.

- In the last section, you can add whatever comments you think are
  necessary.

- At the bottom of the form there is another *Send Request* button to
  submit the request to the Webcast Responsible.

~~~~~~~~~~~~~~~~~~~~~~~~~
Sending a Webcast Request
~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have filled in the form, click either *Send Request*
button to submit the request to the Webcast Responsible.

|figure71|

Figure 71.The *Send Request* button.

Once the request has been submitted, a message will appear at the
top with the current status of the request.

|figure72|

Figure 72. After sending a request, the status will change to
*Request successfully sent* .

The initial status will be *Request successfully sent* . This means
that an email has been sent to the Webcast Responsible with all the
details.

Also, the *Send Request* buttons at the top and the bottom of the
form will disappear and will be replaced by *Modify Request* and
*Withdraw request* buttons.

~~~~~~~~~~~~~~~~~~~~~~~~~~~
Modifying a Webcast Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~

After the request has been sent, you can still modify it. This is
useful if you noticed that you made a mistake or if the Webcast
Responsible asks you to change some of details of it.

Any time you return to the Webcast Request page, information
entered previously will still be there, and you can always change
it and then press the *Modify Request* button to send the request
again.

This will reset the status to *Request successfully sent* , even if
the request had been accepted or rejected previously. The Webcast
Responsible will receive a new mail with the request details.

|figure73|

Figure 73. The *Modify request* and *Withdraw request* buttons.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Withdrawing a Webcast Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can always withdraw a request if you consider it is no longer
necessary. The Webcast Responsible will be notified by mail that
your request has been withdrawn.

After withdrawing a request, the Webcast Request form will return
to its initial state; all the fields will be empty.

~~~~~~~~~~~~~~~~~~~~~
Result of the request
~~~~~~~~~~~~~~~~~~~~~

Once the request is sent, the Webcast Responsible will either
accept or reject it.

If the request is accepted, the status will look as shown in figure
74 below:

|figure74|

Figure 74. The *Request accepted* status.

If the request has been rejected, the status will look as shown in
figure 75 below:

|figure75|

Figure 75. The *Request rejected* status, showing the rejection
reason.

You can see that in this case the responsible has also given you a
reason for his rejection.

In both cases (*accept* and *reject* ), the creator of the event
will receive an email notification.

You can also come back to the page to check on the status, or if
you don not want to reload the page, use the |image1| button to
reload (update) the status.

Even after a request is accepted or rejected, you can still modify
it, which will trigger another mail being sent to the responsible.

*Note: Once the request is accepted, the manager will need to send to every
speaker that will be recorded an email asking to sign the speaker release form.
This will be done through the `Agreements menu <../../UserGuide/EventAgreements.html>`_.


.. |image0| image:: images/html_4108b437.png
.. |image1| image:: images/html_m7f295075.png
.. |image2| image:: images/html_25c4d730.png
.. |image3| image:: images/html_m1976455e.png
.. |image6| image:: images/html_m640d2242.png
.. |image7| image:: images/html_m61d8945b.png
.. |image8| image:: images/html_541e9ff0.png
.. |image9| image:: images/html_4108b437.png
.. |image10| image:: images/html_m6d76c2a0.png
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
.. |figure14| image:: images/html_m4a6d2db3.png
.. |figure15| image:: images/html_m5dc464a0.png
.. |figure16| image:: images/html_32473d75.png
.. |figure17| image:: images/html_m34ab3da5.png
.. |figure18| image:: images/html_45f0f553.png
.. |figure19| image:: images/html_6b114cee.png
.. |figure20| image:: images/html_m719ed08e.png
.. |figure21| image:: images/html_4d7f2740.png
.. |figure54| image:: images/fig54.png
.. |figure55| image:: images/fig55.png
.. |figure56| image:: images/fig56.png
.. |figure57| image:: images/fig57.png
.. |figure58| image:: images/fig58.png
.. |figure59| image:: images/fig59.png
.. |figure60| image:: images/html_m3715592a.png
.. |figure61| image:: images/html_2aee0751.png
.. |figure62| image:: images/html_m61d8945b.png
.. |figure63| image:: images/html_m4a6d2db3.png
.. |figure64| image:: images/html_541e9ff0.png
.. |figure65| image:: images/html_m5dc464a0.png
.. |figure66| image:: images/html_32473d75.png
.. |figure67| image:: images/html_76f03226.png
.. |figure68| image:: images/html_44186de9.png
.. |figure69| image:: images/html_49c4d891.png
.. |figure70| image:: images/html_mce63197.png
.. |figure71| image:: images/html_6380a1b0.png
.. |figure72| image:: images/html_m214468fb.png
.. |figure73| image:: images/html_6c4d7305.png
.. |figure74| image:: images/html_m5dc464a0.png
.. |figure75| image:: images/html_32473d75.png
.. |figure76| image:: images/fig76.png
.. |figure80| image:: images/fig80.png
.. |figure81| image:: images/fig81.png
.. |figure82| image:: images/fig82.png
.. |figure83| image:: images/search_vidyo.png
