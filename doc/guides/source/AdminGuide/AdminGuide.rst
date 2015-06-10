Starting with Indico
====================

Creating an Administration Account
----------------------------------

After installation the first screen presented to you will be:

|image1|

First you must create an user account by clicking on login.
You will be presented with a Log In screen and with an option to
create an account. A form will needs to be filled in with your
user details. Once this is complete an email will be sent to you
with a link to activate your account. Once activated, you will
then be able to login.
Now, it is the moment to add yourself as an Administrator.
In order to do so, click on *Server admin*, in the top blue bar, and you
will access the `Administration Area <#administration-area>`_.

|image2|

From here you need to add your account to the Administrator list,
to do this click on *Add user to list* under the title of *Administrator List*
and use the user search to find and select your account. You will
then be an Administrator and can start using all the features of
Indico. If there is no Administrator account anybody can access and
change all parts of Indico leaving it exposed with no access
control. Once someone adds himself as Administrator, nobody else will be able
to do it in the same way, but existing Administrators can add new Administrators.
Administrators will have access and modification rights to all categories and events.

Users can create their own accounts to use Indico, and they
can modify, delete and add extra logins manually. Administrators are also able
to create new accounts and assign users to be Administrators or
organise users into groups `(see Administration Area) <#administration-area>`_

--------------

Accounts Created by a User
--------------------------

When a new user wants to create an account, he can do so by
clicking on *login* in the top right-hand corner of Indico. From
here he can choose to create an account. A form will be presented
that needs to be filled in with the user's details. Once submitted
an email will be sent to the user.

--------------

Activating a User Created Account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A user activates his account by using the link that is sent in the
email he receives once he applied for a new account. The account must
be activated, otherwise he won't be able to log in.

--------------

Retrieving a Forgotten Password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a user needs to retrieve his password, he can use the
login screen and its forgotten password option; the user will be
sent their password by email to the address registered with that
account.

--------------

Administration Area
==============================

The Administration Area controls the whole of Indico, anything
you modify or add from here can be used throughout the whole
program. From here you can change general information about your
version of Indico, manually add, activate and modify accounts, add
more than one login for a user, delete additional logins and
assign users to groups You can also define domains for use with
Access Control throughout Indico and you have control of any
maintenance.

--------------

General settings
----------------

From the *General settings* in the Administration Area, you are able to
modify the system title, the organisation, the support email, the no
reply email and address. You can also add or remove users from the
administration list; this means they have full administration access
throughout Indico.

|image3|

The Support email address you add in the General System
Information will appear as the overall general support contact.
However, if a problem occurs within the program and an error
report needs to be sent, this report will be sent to the developers not to
this support email.

--------------

Users
-----

The *Users and Groups* option allows you to control and modify any of
the users accounds and groups.


--------------

Searching for Users
~~~~~~~~~~~~~~~~~~~

You can search for a user by surname, first name, email address or organisation.
If you are not sure of the full details you can enter only one of the options or
the first few letters and you will be shown all the users that match your
search. The Search filter is found by clicking on *Users*. User profiles can be
accessed and modified by clicking on the results.


--------------

Groups
------

You can use the Groups section to categorise users if you wish.
You may want to use this feature to help with Access Control.
If, for example, you have more than one user that you would like to
manage an event, you could make a group of Managers for each event
and then assign each set to an event, as apposed to adding each
individual user.

To create a new group use the *Create new Group* feature in the *Groups* menu.
You will be asked for a group name and users to add.

You can assign a group of users to Access Control in the same way
as you can add individual users. Once your group(s) is/are created
you can use the *Search Groups* option to find a particular group, to
continue adding and removing users, or to modify the group details.

--------------

IP Domains
----------

You can add sets of IP addresses called Domains to be used in
Access Control. To add a new domain use the *New Domain* option in
the *IP Domains* menu.

You can then enter a name, description, and the IP addresses you
which to use in this domain:

|image9|

Any domains you create can be viewed from the  *IP Domains*
menu, you can search for the domain name you want to look at it
and you will be shown its details.

|image10|

You can also modify the Domain by clicking on it, and then on the
button *modify*.

--------------

Maintenance
-----------

The maintenance area is accessible from the *System* menu, *Maintenance* tab.
From here you are able to:

-
   View the amount of Temporary files being used by Indico. Indico
   creates temporary files internally for example when a user submits
   a file or when creating a DVD, etc. These temporary files are
   stored until you delete them from here.

-
   Pack the Database. Indico periodically backs up your database and
   stores the older versions; you can choose to remove older versions
   to save memory by using the *pack* option, this will keep the
   current version of the database.


|image11|

--------------

Administration scripts
========================


Recover Administration Account
--------------------------------

*indico_admin* script allows you to recover any administrator account.
It can:

* grant administrator privileges to any existing user (by user id)
* revoke administrator privileges from any existing user (by user id)
* create a new user with administrator privileges

For more information type in console ::

    indico_admin --help


.. |image0| image:: AdminGuidePics/logo.png
.. |image1| image:: AdminGuidePics/start1.png
.. |image2| image:: AdminGuidePics/start2.png
.. |image3| image:: AdminGuidePics/admin1.png
.. |image4| image:: AdminGuidePics/admin2.png
.. |image9| image:: AdminGuidePics/admin7.png
.. |image10| image:: AdminGuidePics/admin8.png
.. |image11| image:: AdminGuidePics/admin9.png
