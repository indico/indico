Changelog
=========


Version 2.1
-----------

*Unreleased*

Major Features
^^^^^^^^^^^^^^

- Add event roles, which are similar to local groups but within the
  scope of an event. They can be used both for assigning permissions
  within the event and also for quickly seeing which user has which
  role (such as "Program Committee" in the event
- Add new *Participant Roles* (previously called *Roles*) which
  now shows each person's custom event roles and whether they have
  registered for the event in addition to the the default roles
  (speaker, chairperson, etc.)
- Add visibility options to custom abstract/contribution fields
  so they can be restricted to be editable/visible only for event
  managers or authors/submitters instad of anyone who can see the
  abstract/contribution
- Provide new interface to import registations/contributions from a CSV
  file (:issue:`3144`)
- Rework how access/permissions are managed. Now all access and management
  privileges can be assigned from a single place on the protection
  management page.

Improvements
^^^^^^^^^^^^

- Allow specifying a default session for a track which will then be
  used by default when accepting an abstract in that track (:issue:`3069`)
- Allow marking contribution types as private so they cannot be selected
  by users submitting an abstract (:issue:`3138`)
- Add support for boolean (yes/no) and freetext questions in abstract
  reviewing (:issue:`3175`)
- Support event cloning with monthly recurrence on the last day of the
  month (:issue:`1580`)
- Add support for custom session types (:issue:`3189`)
- Move poster session flag from session settings to session type settings
- Add contribution cloning within an event (:issue:`3207`)
- Add option to include the event description in reminder emails
  (:issue:`3157`, thanks :user:`bpedersen2`)
- Pin default themes to the top for event managers (:issue:`3166`)
- Add user setting whether to show future events or not by default in a
  category. Also keep the per-category status in the session (:issue:`3233`,
  thanks :user:`bpedersen2`)
- Keep page titles in sync with conference menu item titles (:issue:`3236`)
- Add option to hide an attachment folder in the display areas of an event
  (:issue:`3181`, thanks :user:`bpedersen2`)
- Improve flower redirect URI generation (:issue:`3187`, thanks
  :user:`bpedersen2`)
- When blocking a user account, the user will be forcefully logged out in
  addition to being prevented from logging in
- Show track-related columns in abstract list only if there are tracks
  defined for the event (:issue:`2813`)
- Show warning box to inform that reviewer roles do not apply when an event
  has no tracks (:issue:`2919`)
- Allow specifying min/max length for registration form text fields
  (:issue:`3193`, thanks :user:`bpedersen2`)
- Add settings to configure the scale of 'rating' questions in paper
  reviewing
- Show a nicer error message when entering an excessively high base
  registration fee (:issue:`3260`)
- Use proper British English for person titles (:issue:`3279`)
- Add event keywords in meta tags (:issue:`3262`, thanks :user:`bpedersen2`)
- Improve sorting by date fields in the registrant list
- Use the user's preferred name format in more places
- Add "back to conference" link when viewing a conference timetable using
  a meeting theme (:issue:`3297`, thanks :user:`bpedersen2`)
- Allow definition lists in places where Markdown or HTML is accepted
  (:issue:`3325`)
- Include event date/time in registration emails (:issue:`3337`)
- Allow div/span/pre with classes when writing raw HTML in CKEditor
  (:issue:`3332`, thanks :user:`bpedersen2`)
- Sort abstract authors/speakers by last name (:issue:`3340`)
- Improve machine-readable metadata for events and categories
  (:issue:`3287`, thanks :user:`bpedersen2`)

Bugfixes
^^^^^^^^

- Fix selecting a person's title in a different language than English
- Fix display issue in "now happening" (:issue:`3278`)
- Fix error when displaying the value of an accommodation field in the
  registrant list and someone has the "no accomodation" option selected
  (:issue:`3272`, thanks :user:`bpedersen2`)
- Use the 'Reviewing' realm when logging actions from the abstract/paper
  reviewing modules
- Fix error when printing badges/posters with empty static text fields
  (:issue:`3290`)
- Fix error when generating a PDF timetable including contribution
  abstracts (:issue:`3289`)
- Do not require management access to a category to select a badge
  template from it as a backside.
- Fix breadcrumb metadata (:issue:`3321`, thanks :user:`bpedersen2`)
- Fix error when accessing certain registration pages without an active
  registration

Internal Changes
^^^^^^^^^^^^^^^^

- Rename *Roles* in ACL entries to *Permissions*.  This especially affects
  the ``can_manage`` method whose ``role`` argument has been renamed to
  ``permission`` (:issue:`3057`)
- Add new ``registration_checkin_updated`` signal that can be used by
  plugins to perform an action when the checkin state of a registration
  changes (:issue:`3161`, thanks :user:`bpedersen2`)
- Add new signals that allow plugins to run custom code at the various
  stages of the ``RH`` execution and replace/modify the final response
  (:issue:`3227`)
- Add support for building plugin wheels with date/commit-suffixed
  version numbers (:issue:`3232`, thanks :user:`driehle`)


----


Version 2.0.3
-------------

*Released on March 15, 2018*

Security fixes
^^^^^^^^^^^^^^

- Do not show contribution information (metadata including title, speakers
  and a partial description) in the contribution list unless the user has
  access to a contribution

Improvements
^^^^^^^^^^^^

- Show more suitable message when a service request is auto-accepted
  (:issue:`3264`)


Version 2.0.2
-------------

*Released on March 07, 2018*

Security fixes
^^^^^^^^^^^^^^

- Update `bleach <https://github.com/mozilla/bleach>`_ to fix an XSS vulnerability

Improvements
^^^^^^^^^^^^

- Warn when editing a speaker/author would result in duplicate emails

Bugfixes
^^^^^^^^

- Take 'center' orientation of badge/poster backgrounds into account
  (:issue:`3238`, thanks :user:`bpedersen2`)
- Fail nicely when trying to register a local account with an already-used
  email confirmation link (:issue:`3250`)


Version 2.0.1
-------------

*Released on February 6, 2018*

Improvements
^^^^^^^^^^^^

- Add support for admin-only designer placeholders. Such placeholders
  can be provided by custom plugins and only be used in the designer
  by Indico admins (:issue:`3210`)
- Sort contribution types alphabetically
- Add folding indicators when printing foldable badges (:issue:`3216`)

Bugfixes
^^^^^^^^

- Fix LaTeX rendering issue when consecutive lines starting with ``[``
  were present (:issue:`3203`)
- Do not allow managers to retrieve tickets for registrants for whom
  ticket access is blocked by a plugin (:issue:`3208`)
- Log a warning instead of an exception if the Indico version check
  fails (:issue:`3209`)
- Wrap long lines in event log entries instead of truncating them
- Properly show message about empty agenda in reminders that have
  "Include agenda" enabled but an empty timetable
- Fix overly long contribution type names pushing edit/delete buttons
  outside the visible area (:issue:`3215`)
- Only apply plugin-imposed ticket download restrictions for tickets,
  not for normal badges.
- Fix switching between badge sides in IE11 (:issue:`3214`)
- Do not show poster templates as possible backsides for badges
- Convert alpha-channel transparency to white in PDF backgrounds
- Make number inputs big enough to show 5 digits in chrome
- Sort chairperson list on lecture pages
- Remove whitespace before commas in speaker lists
- Hide author UI for subcontribution speakers (:issue:`3222`)


Version 2.0
-----------

*Released on January 12, 2018*

Improvements
^^^^^^^^^^^^

- Add ``author_type`` and ``is_speaker`` fields for persons in the JSON
  abstract export
- Add legacy redirect for ``conferenceTimeTable.py``

Bugfixes
^^^^^^^^

- Fix unicode error when searching external users from the "Search
  Users" dialog
- Fix missing event management menu/layout when creating a material
  package from the event management area
- Fix error when viewing a contribution with co-authors
- Fix sorting of registration form items not working anymore after
  moving/disabling some items
- Fix error after updating from 2.0rc1 if there are cached Mako
  templates
- Fix error when retrieving an image referenced in an abstract fails
- Fix rendering of time pickers in recent Firefox versions (:issue:`3194`)
- Fix error when trying to use the html serializer with the timetable API
- Fix error when receiving invalid payment events that should be ignored
- Fix last occurrence not being created when cloning events (:issue:`3192`)
- Fix multiple links in the same line being replaced with the first one
  when converting abstracts/contributions to PDF (:issue:`2816`)
- Fix PDF generation when there are links with ``&`` in the URL
- Fix incorrect spacing in abstract author/speaker lists (:issue:`3205`)


Version 2.0rc2
--------------

*Released on December 8, 2017*

Improvements
^^^^^^^^^^^^

- Allow changing the reloader used by the dev server (:issue:`3150`)

Bugfixes
^^^^^^^^

- Do not show borders above/below the message in registration emails
  unless both the header and body blocks are used (:issue:`3151`)
- Roll-back the database transaction when an error occurs.
- Fix rendering of the LaTeX error box (:issue:`3163`)
- Fix "N/A" being displayed in a survey result if 0 is entered in
  a number field
- Fix "N/A" not being displayed in a survey result if nothing is
  selected in a multi-choice select field
- Fix error when using ``target_*`` placeholders in abstract
  notification emails for actions other than "Merged" (:issue:`3171`)
- Show full track title in tooltips on abstract pages
- Show correct review indicators when a reviewer still has to review
  an abstract in a different track
- Fix unicode error when searching external users in an LDAP backend

Internal Changes
^^^^^^^^^^^^^^^^

- Remove ``SCSS_DEBUG_INFO`` config option.


Version 2.0rc1
--------------

*Released on November 10, 2017*

Improvements
^^^^^^^^^^^^

- Hide category field in event creation dialog if there are no
  subcategories (:issue:`3112`)
- Remove length limit from registration form field captions (:issue:`3119`)
- Use semicolons instead of commas as separator when exporting list
  values (such as multi-select registration form fields) to CSV or
  Excel (:issue:`3060`)
- Use custom site title in page title (:issue:`3018`)
- Allow manually entering dates in datetime fields (:issue:`3136`)
- Send emails through a celery task. This ensures users do not get
  an error if the mail server is temporarily unavailable. Sending an
  email is also retried for a while in case of failure. In case of a
  persistent failure the email is dumped to the temp directory and
  can be re-sent manually using the new ``indico resend_email``
  command (:issue:`3121`)
- Reject requests containing NUL bytes in the query string (:issue:`3142`)

Bugfixes
^^^^^^^^

- Do not intercept HTTP exceptions containing a custom response.
  When raising such exceptions we do not want the default handling
  but rather send the custom response to the client.
- Do not apply margin for empty root category sidebar (:issue:`3116`,
  thanks :user:`nop33`)
- Fix alignment of info-grid items on main conference page (:issue:`3126`)
- Properly align the label of the attachment folder title field
- Fix some rare unicode errors during exception handling/logging
- Clarify messages in session block rescheduling dialogs (:issue:`3080`)
- Fix event header bar in IE11 (:issue:`3135`)
- Fix footer on login page (:issue:`3132`)
- Use correct module name for abstract notification emails in the event log
- Remove linebreaks from email subject in paper review notifications
- Fix extra padding in the CFA roles dialog (:issue:`3129`)
- Do not show an extra day in timetable management if an event begins
  before a DST change
- Disable caching when retrieving the list of unscheduled contributions
- Process placeholders in the subject when emailing registrants
- Fix Shibboleth login with non-ascii names (:issue:`3143`)

Internal Changes
^^^^^^^^^^^^^^^^

- Add new ``is_ticket_blocked`` signal that can be used by plugins to
  disable ticket downloads for a registration.


Version 2.0a1
-------------

*Released on October 20, 2017*

This is the first release of the 2.0 series, which is an almost complete
rewrite of Indico based on a modern software stack and PostgreSQL.
