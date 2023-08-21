Changelog
=========


Version 3.3
-----------

*Unreleased*

Major Features
^^^^^^^^^^^^^^

- Nothing so far

Internationalization
^^^^^^^^^^^^^^^^^^^^

- Nothing so far

Improvements
^^^^^^^^^^^^

- Invalidate password reset links once the password has been changed (:pr:`5878`)
- Add full ACLs for custom conference menu items, instead of just being able to
  restrict them to speakers or registrants (:pr:`5670`, thanks :user:`kewisch`)
- Make editing timeline display much more straightforward (:pr:`5674`)
- Allow event managers to delete editables from contributions (:pr:`5778`, :pr:`5892`)
- Allow room managers to add internal notes to bookings (:issue:`5746`, :pr:`5791`)
- Support generating tickets and badges for each of the registrant's accompanying
  persons (:pr:`5424`)
- Add keyboard shortcut (CTRL-SHIFT-A) to toggle room booking admin override (:pr:`5909`)
- Improve login page UI, allow overriding the logo URL (:data:`LOGIN_LOGO_URL` config option)
  and using custom logos for auth providers (``logo_url`` in the auth provider settings)
  (:pr:`5936`, thanks :user:`openprojects`)
- Show only active registration counts on the registration form management dashboard, and add
  an inactive registration count to the registration list (:pr:`5990`)
- Store creation date of users and show it to admins (:pr:`5957`, thanks :user:`vasantvohra`)
- Add option to hide links to Room Booking system for users who lack access (:pr:`5981`,
  thanks :user:`SegiNyn`)
- Support weekly room bookings that take place on multiple weekdays (:pr:`5829`, :pr:`6000`,
  :issue:`5806`)
- Hide events marked as invisible from builtin search results unless the user is a manager
  (:pr:`5947`, thanks :user:`openprojects`)
- Support sessions that expire at a certain date (specified by the used flask-multipass
  provider) regardless of activity when using an external login method (:pr:`5907`, thanks
  :user:`cbartz`)
- Allow configuring future months threshold for categories (:issue:`2984`, :pr:`5928`, thanks
  :user:`kewisch`)
- Allow editors to edit their review comments on editables (:pr:`6008`)
- Auto-linking of patterns in minutes (e.g. issue trackers, Github repos...) (:pr:`5998`)
- Log editor actions in the Editing module (:pr:`6015`)
- Grant subcontribution speakers submission privileges by default in newly created events
  (:issue:`5905`, :pr:`6025`)
- Stop overwhelmingly showing past events in the 'Events at hand' section in the user dashboard
  (:pr:`6049`)
- Add document templates to generate PDF receipts, certificates, and similar documents for
  event participants (:pr:`5123`, :pr:`6078`)
- Show which persons are external in the user search dialog (:pr:`6074`)
- Add feature for users to export all data linked to them (:pr:`5757`)
- Add Outlook online calendar button to share widget (:issue:`6075`, :pr:`6077`)
- Remove Facebook and Google+ share widgets and make Twitter share button privacy-friendly
  (:pr:`6077`)

Bugfixes
^^^^^^^^

- Prevent room booking sidebar menu from overlapping with the user dropdown menu
  (:pr:`5910`)
- Allow cancelling pending bookings even if they have already "started" (:pr:`5995`)
- Disallow switching the repeat frequency of an existing room booking from weekly to monthly
  or vice versa (:pr:`5999`)
- Ignore deleted fields when computing the number of occupied slots for a registration (:pr:`6035`)
- Show the description of a subcontribution in conference events (:issue:`5946`, :pr:`6056`)
- Only block templates containing a QR code via ``is_ticket_blocked`` (:pr:`6062`)

Accessibility
^^^^^^^^^^^^^

- Include current language in page metadata (:pr:`5894`, thanks :user:`foxbunny`)
- Make language list accessible (:issue:`5899`, :pr:`5903`, thanks :user:`foxbunny`)
- Add accessible label to the main page link (:issue:`5934`, :pr:`5935`, thanks
  :user:`foxbunny`)
- Add bypass block links (:issue:`5932`, :pr:`5939`, thanks :user:`foxbunny`)
- Make search fields more accessible (:issue:`5948`, :pr:`5950`, thanks :user:`foxbunny`)
- Make search result status messages more accessible (:issue:`5949`, :pr:`5950`,
  thanks :user:`foxbunny`)
- Make search results tabs accessible (:issues:`5964`, :pr:`5965`, thanks :user:`foxbunny`)
- Make timezone list accessible (:issue:`5908`, :pr:`5914`, thanks :user:`foxbunny`)
- Make "Skip access checks" checkbox in search keyboard-accessible (:issue:`5952`, :pr:`5953`,
  thanks :user:`foxbunny`)
- Prevent icons from being announced to screen readers as random characters (:issue:`5985`,
  :pr:`5986`, thanks :user:`foxbunny`)
- Add proper labels to the captcha play and reload buttons (:issue:`6064`, :pr:`6080`,
  :thanks:`foxbunny`)
- Associate form labels with form controls in the registration form (:issue:`6059`, :issue:`6073`,
  :pr:`6076`, thanks :user:`foxbunny`)
- Make dropdown menu fully accessible (:issue:`5896`, :pr:`5897`, thanks :user:`foxbunny`)

Internal Changes
^^^^^^^^^^^^^^^^

- Use (dart-)sass instead of the deprecated node-sass/libsass for CSS compilation
  (:pr:`5734`)
- Add ``event.is_field_data_locked`` signal, allowing plugins to lock registration form
  fields on a per-registration basis (:pr:`5424`)
- Replace WYSIWYG (rich-text) editor with TinyMCE, due to the license and branding
  requirements of the previous editor (:pr:`5938`)
- Add a new Indico design system (:pr:`5914`, thanks :user:`foxbunny`)
- Add ``event.registration_form_field_deleted`` signal, allowing plugins to handle
  the removal of registration form fields (:pr:`5924`)
- Add a tool ``bin/managemnent/icons_generate.py`` to generate CSS for icomoon icons based
  on ``selection.json`` (:pr:`5986`, thanks :user:`foxbunny`)
- Pass form class arguments to ``core.add_form_fields`` signal handlers (:pr:`6020`, thanks
  :user:`vtran99`)
- Support Python 3.12 (:pr:`5978`)
- Remove watchman reloader support, use watchfiles instead (:pr:`5978`)
- Improve ``indico i18n`` CLI to support plugin-related i18n operations (:issue:`5906`, :pr:`5961`,
  thanks :user:`SegiNyn`)
- Use `ruff <https://docs.astral.sh/ruff/>`_ for linting Python code (:pr:`6037`)
- Add ``<ind-menu>`` custom element for managing drop-down menus (:issue:`5896`, :pr:`5897`,
  thanks :user:`foxbunny`)


----


Version 3.2.9
-------------

*Unreleased*

Security fixes
^^^^^^^^^^^^^^

- Update `Werkzeug <https://pypi.org/project/Werkzeug/>`_ library due to a
  DoS vulnerability while parsing certain file uploads (:cve:`CVE-2023-46136`)

Improvements
^^^^^^^^^^^^

- Add placeholders for accompanying persons to the badge/ticket designer (:pr:`6033`)

Bugfixes
^^^^^^^^

- Fix meeting timetable not showing custom locations when all top-level timetable
  entries are session blocks inheriting the custom location from its session (:pr:`6014`)
- Always show exact matches when searching for existing videoconference rooms to attach to an
  event (:pr:`6022`)
- Include materials linked to sessions in the material package (:pr:`6024`)
- Use the correct locale when sending sending email notifications to others in an event
  (:issue:`5987`, :pr:`6021`)
- Fix the author/speaker selector (e.g. for abstracts) breaking when submitting the form and
  getting a validation error (:issue:`6043`, :pr:`6053`)
- Do not cancel past linked room bookings when deleting an event (:issue:`6032`, :pr:`6051`)
- Fix contribution list filters being obscured by the action dialog (:pr:`6055`)

Internal Changes
^^^^^^^^^^^^^^^^

- None so far


Version 3.2.8
-------------

*Released on October 11, 2023*

Security fixes
^^^^^^^^^^^^^^

- Update `Pillow <https://pypi.org/project/Pillow/>`_ library due to
  vulnerabilities in libwebp (:cve:`CVE-2023-4863`)

Internationalization
^^^^^^^^^^^^^^^^^^^^

- New translation: Italian

Bugfixes
^^^^^^^^

- Fix error when sending registration invitation reminders (:issue:`5879`, :pr:`5880`,
  thanks :user:`bpedersen2`)
- Fix accessing the conference overview page when the default conference home page is
  set to a custom page (:pr:`5882`)
- Show percentages for multi-choice survey answers based on number of answers instead of
  total number of choices selected (:pr:`5930`)


Version 3.2.7
-------------

*Released on August 02, 2023*

Bugfixes
^^^^^^^^

- Fix not being able to remove the last entry from a room ACL (:pr:`5863`, thanks
  :user:`SegiNyn`)
- Fix conditional fields remaining hidden in abstract judgment form (:pr:`5873`)


Version 3.2.6
-------------

*Released on July 20, 2023*

Security fixes
^^^^^^^^^^^^^^

- Fix an XSS vulnerability in various confirmation prompts commonly used when deleting
  things. Exploitation requires someone with at least submission privileges (such as a
  speaker) and then rely on someone else to attempt to delete this content. However,
  considering that event organizers may indeed delete suspicious-looking content when
  encountering it, there is a non-negligible risk of such an attack to succeed. Because
  of this it is strongly recommended to upgrade as soon as possible (:pr:`5862`,
  :cve:`CVE-2023-37901`)

Internationalization
^^^^^^^^^^^^^^^^^^^^

- New translation: Czech

Improvements
^^^^^^^^^^^^

- Show which files were added or modified on each editing timeline revision (:pr:`5802`)
- Support rendering Japanese, Chinese & Korean letters in PDFs (:issue:`3120`, :pr:`5842`,
  thanks :user:`adamjenkins`)
- Add button to adapt columns widths on the reviewing area's abstracts list (:pr:`5837`)
- Allow cloning category-level badge/poster templates into another category (:pr:`5775`,
  thanks :user:`SegiNyn`)
- Allow using a custom link text in the ``{event_link}`` email placeholder, using the
  ``{event_link:something-else-here}`` syntax (:issue:`5858`, :pr:`5860`)
- Add option to add "event cancelled" semantics for event labels, which will disable
  reminders for events having this label (:issue:`5285`, :pr:`5861`)

Bugfixes
^^^^^^^^

- Use correct name formatting in person link fields (:pr:`5835`)

Internal Changes
^^^^^^^^^^^^^^^^

- Support Python 3.11


Version 3.2.5
-------------

*Released on June 26, 2023*

Security fixes
^^^^^^^^^^^^^^

- Fix an XSS vulnerability in the LaTeX ``\href`` macro when rendering it client-side.
  Previously, it was possible to embed arbitrary JavaScript there using the ``javascript:``
  protocol. The underlying MathJax library has now been updated to version 3 which allows
  blacklisting certain protocols, thus allowing only ``http``, ``https`` and ``mailto``
  links in ``\href`` macros (:pr:`5818`)

Improvements
^^^^^^^^^^^^

- Show actual recipient data in the email preview instead of the that of the event creator
  (:pr:`5794`)
- Add an option to set a maximum number of choices in a multi-choice field (:pr:`5800`)

Bugfixes
^^^^^^^^

- Fix width of time column in PDF timetable when using 12-hour time format (:pr:`5788`)
- Fix wrong date in email subject for room booking occurrence cancellations (:pr:`5790`)
- Fix excessive queries being sent in meetings that have registration form with limited
  places and many registrants (:pr:`5799`)
- Fix extremely slow query when retrieving list of registration forms in conferences with
  many registrants while not logged in (:pr:`5799`)
- Fix title of session conveners being always empty in HTTP API with XML serialization
  (:pr:`5813`)
- Fix editable filters not working simultaneously with editable search (:pr:`5796`)
- Fix missing icons in Abstract Markdown editor (:pr:`5815`)
- Fix text overflow in event manage button (:pr:`5816`)
- Fix undone revisions being used instead of the latest valid one when downloading
  revision files as a ZIP archive (:pr:`5820`)
- Fix custom actions not showing on revisions if the latest revision has been undone
  (:pr:`5820`)

Internal Changes
^^^^^^^^^^^^^^^^

- Some basic but useful docs for the Registration Form model classes


Version 3.2.4
-------------

*Released on May 26, 2023*

Security fixes
^^^^^^^^^^^^^^

- Set ``Vary: Cookie`` header when session data is present and used. This ensures
  that data linked to a (logged-in) session cannot leak between requests even in case
  of a poorly-configured caching proxy in front of Indico (:pr:`5753`)

Improvements
^^^^^^^^^^^^

- Use the revision's timestamp when downloading its files as a ZIP archive (:pr:`5686`)
- Use more consistent colors on the editing judgment button (:issue:`5687`, :pr:`5697`)
- Keep history when undoing judgments on editables (:pr:`5630`)
- Add search field to the abstracts list for reviewers (:issue:`5698`, :pr:`5703`)
- Align status box colors with judgment dropdown (:issue:`5699`, :pr:`5706`)
- Use a gender-neutral chairperson icon (:pr:`5710`)
- Add option to set the abstracts' primary authors as the default submitters for the
  corresponding contributions (:pr:`5711`)
- Allow commenting on accepted/rejected editables (:issue:`5712`, :pr:`5722`)
- Hide deleted sections and fields from registration summary (:pr:`5716`)
- Add support for authorized submitters in Call for Papers (:pr:`5728`)
- Display abstract submission comment in the list of abstracts (:pr:`5733`)
- Allow searching for contributions by author in the management area (:pr:`5742`)
- Include start/end dates of the whole booking in the timeline tooltip of recurring
  room bookings (:issue:`5730`, :pr:`5740`)
- Add day of the week to room booking details modal and timeline (:issue:`5718`,
  :pr:`5743`)
- Allow acceptance and rejection of editables in the editable list (:pr:`5721`)
- Email verification attempts during signup now trigger rate limiting to prevent
  spamming large amounts of confirmation emails (:pr:`5727`)
- Allow bulk-commenting editables in the editable list (:pr:`5747`)
- Allow emailing contribution persons that have not yet made any submissions to a
  given editable type (:pr:`5755`)
- Show only "ready to review" editables on the "get next editable" list (:pr:`5765`)
- Disallow uploading empty files (:pr:`5767`)
- Include non-speaker authors in the timetable export API (:issue:`5412`, :pr:`5738`)
- Add setting to force track selection when accepting abstracts (:pr:`5771`)
- Log detailed changes when editing contributions (:pr:`5777`)
- Allow managers to ignore required field restrictions in registration forms
  (:issue:`5644`, :pr:`5682`, thanks :user:`kewisch`)
- Allow selecting the global noreply address as the sender for event reminders
  (:pr:`5784`)
- Allow admins to change the password of local accounts (:pr:`5789`, thanks
  :user:`omegak`)

Bugfixes
^^^^^^^^

- Fix creating invited abstracts (:pr:`5696`)
- Fix error on contribution page when there is no paper but the peer reviewing module
  is enabled and configured to hide accepted papers
- Clone all protection settings (in particular submitter privileges) when cloning events
  (:pr:`5702`)
- Fix searching in single-choice dropdown fields in registration forms (:pr:`5709`)
- Fix uploading files in registration forms where the user only has access through the
  registration's token (:pr:`5719`)
- Fix being unable to set the "speakers and authors" as the default contribution
  submitter type (:pr:`5711`)
- Check server-side if Call for Papers is open when submitting a paper (:pr:`5725`)
- Fix room notification email list showing up empty when editing it (:issue:`5729`,
  :pr:`5731`)
- Fix performance issues in paper assignment list (:pr:`5736`)
- Fix performance issues in event export API with large events when including
  contributions (:pr:`5736`)
- Fix error when a search query matches content from unlisted events (:issue:`5759`,
  :pr:`5761`)
- Fix ToS and Privacy Policy links in room booking module not working when using an
  external URL (:pr:`5774`)
- Do not apply default values to new registration form fields when editing an existing
  registration (:pr:`5781`)
- Allow ``0`` for a required registration form numbe field (unless a higher minimum
  value is set) (:pr:`5781`)

Internal Changes
^^^^^^^^^^^^^^^^

- Update Python & JavaScript dependencies (:pr:`5726`, :pr:`5752`)
- Add support for the watchfiles live reloader (:pr:`5732`)
- Add an endpoint to allow resetting the state of an accepted editable to "ready to
  review" (:pr:`5758`)
- Add RESTful endpoints for custom contribution fields (:pr:`5768`)


Version 3.2.3
-------------

*Released on February 23, 2023*

Security fixes
^^^^^^^^^^^^^^

- Sanitize HTML in global announcement messages
- Update `cryptography <https://pypi.org/project/cryptography/>`_ library due to
  vulnerabilities in OpenSSL (:cve:`CVE-2023-0286`)
- Update `werkzeug <https://pypi.org/project/werkzeug/>`_ library due to a potential
  Denial of Service vulnerability (:cve:`CVE-2023-25577`)

.. note::

    The risk of malicious HTML (e.g. scripts) in the global announcement is minimal
    as only Indico administrators can set such an announcement anyway. However, in the
    unlikely case that an administrator becomes malicious or is compromised, they would
    have been be able to perform XSS against their Indico instance.

Improvements
^^^^^^^^^^^^

- Include co-authors in abstract list columns and spreadsheet exports (:pr:`5605`)
- Include speakers in abstract list columns and spreadsheet exports (:pr:`5615`)
- Add an option to export all events in a series to ical at once (:issue:`5617`, :pr:`5620`)
- Make it possible to load more events in series management (:pr:`5629`)
- Check manually entered email addresses of speakers/authors/chairpersons
  to avoid collisions and inconsistencies (:pr:`5478`)
- Add option to use review track as accepted track when bulk-accepting abstracts
  (:pr:`5608`)
- Add setting to only allow managers to upload attachments to events and
  contributions (:pr:`5597`)
- Support Markdown when writing global announcement and apply standard HTML
  sanitization to the message (:pr:`5640`)
- Add BCC field on contribution email dialogs (:pr:`5637`)
- Allow filtering by location in room booking (:issue:`4291`, :pr:`5622`,
  thanks :user:`mindouro`)
- Add button to adapt column widths in paper & contribution lists (:pr:`5642`)
- Add event language settings to set default and additional languages (:issue:`5606`,
  :pr:`5607`, thanks :user:`vasantvohra`)
- Fail nicely when trying to import an event from another Indico instance (:issue:`5619`,
  :pr:`5653`)
- Add option to send reminders to invited registrants who have not yet responded
  (:issue:`5579`, :pr:`5654`)
- Hide the top box with the latest files of an editable until it has been accepted
  and published (:issue:`5660`, :pr:`5665`)
- Allow uploading files when requesting changes on the editing timeline (:pr:`5612`)
- Add ``locked_fields`` to the identity provider settings in ``indico.conf`` to
  prevent non-admin users from turning off their profile's personal data
  synchronization (:pr:`5648`)
- Add an option to sync event persons with users (:pr:`5677`)
- Disallow repeated filenames in editing revisions (:pr:`5681`)
- Add setting to hide peer-reviewed papers from participants even after they have
  been accepted (:issue:`5666`, :pr:`5671`)
- Prevent concurrent assignment of editors to editables (:pr:`5684`)
- Add color labels to the filter dropdown (:issue:`5675`, :pr:`5680`)

Bugfixes
^^^^^^^^

- Correctly show contribution authors in participant roles list (:pr:`5603`)
- Disable Sentry trace propagation to outgoing HTTP requests (:pr:`5604`)
- Include token in notification emails for private surveys (:pr:`5618`)
- Fix some API calls not working with personal access tokens (:pr:`5627`)
- Correctly handle paragraphs and linebreaks in plaintext conversion (:pr:`5623`)
- Send manager notifications and email participant if they withdraw from an event
  (:issue:`5633`, :pr:`5638`, thanks :user:`kewisch`)
- Do not break registrations with purged accommodation fields (:issue:`5641`,
  :pr:`5643`)
- Do not show blocked rooms as available on the very last day of the blocking
  (:pr:`5663`)
- Do not show blocked rooms as available for admins unles they have admin override
  mode enabled (:pr:`5663`)
- Fix roles resetting to the default ones when editing person data in an abstract
  or contribution (:pr:`5664`)
- Correctly show paragraphs in CKEditor fields (:issue:`5624`, :pr:`5656`, thanks
  :user:`kewisch`)
- Fix empty iCal file being attached when registering for a protected event
  (:pr:`5688`)

Internal Changes
^^^^^^^^^^^^^^^^

- Add ``rh.before-check-access`` signal (:pr:`5639`, thanks :user:`omegak`)
- Add ``indico celery --watchman ...`` to run Celery with the Watchman reloader
  (:pr:`5667`)
- Allow overriding the cache TTL for remote group membership checks (:pr:`5672`)
- Allow a custom editing workflow service to mark new editables as ready-for-review
  without creating a new replacement revision (:pr:`5668`)
- Update Python dependencies (:pr:`5689`)


Version 3.2.2
-------------

*Released on December 09, 2022*

Improvements
^^^^^^^^^^^^

- Display program codes in 'My contributions' (:pr:`5573`)
- Warn when a user cannot create an event in the current category (:pr:`5572`)
- Display all contributions in 'My contributions' and not just those with
  submitter privileges (:pr:`5575`)
- Apply stronger sanitization on rich-text content pasted into CKEditor
  (:issue:`5560`, :pr:`5571`)
- Allow raw HTML snippets when editing custom conference pages and event
  descriptions (:issue:`5584`, :pr:`5587`)
- Warn more clearly that link attachments are just a link and do not copy
  the file (:issue:`5551`, :pr:`5593`)
- Add option to email people with specific roles about their contributions
  or abstracts (:pr:`5598`)
- Add setting to allow submitters to edit custom fields in their contributions
  (:pr:`5599`)

Bugfixes
^^^^^^^^

- Fix broken links in some notification emails (:pr:`5567`)
- Fix always-disabled submit button when submitting an agreement response
  on someone's behalf (:pr:`5574`)
- Disallow nonsensical retention periods and visibility durations (:pr:`5576`)
- Fix sorting by program code in editable list (:pr:`5582`)
- Do not strip custom CSS classes from HTML in CKEditor (:issue:`5584`, :pr:`5585`)
- Use the instance's default locale instead of "no locale" (US-English) in places
  where no better information is known for email recipients (:pr:`5586`)

Internal Changes
^^^^^^^^^^^^^^^^

- Refactor email-sending dialog using React (:pr:`5547`)


Version 3.2.1
-------------

*Released on November 10, 2022*

Security fixes
^^^^^^^^^^^^^^

- Update `cryptography <https://pypi.org/project/cryptography/>`_ library due to
  vulnerabilities in OpenSSL (:cve:`CVE-2022-3602`, :cve:`CVE-2022-3786`)

.. note::

    We do not think that Indico is affected by those vulnerabilities as it does
    not use the *cryptography* library itself, and the dependency that uses it
    is only used during SSO (OAuth) logins and most likely in a way that is not
    vulnerable. It is nonetheless recommended to update as soon as possible.

Internationalization
^^^^^^^^^^^^^^^^^^^^

- Make email templates translatable (:issue:`5263`, :pr:`5488`, thanks :user:`Leats`)

Improvements
^^^^^^^^^^^^

- Enable better image linking UI in CKEditor (:pr:`5492`)
- Restore the "fullscreen view" option in CKEditor (:pr:`5505`)
- Display & enforce judging deadline (:pr:`5506`)
- Add a setting to disable entering persons in person link fields manually (:pr:`5499`)
- Allow taking minutes in markdown (:issue:`3386`, :pr:`5500`, thanks :user:`Leats`)
- Add setting to preselect "Include users with no Indico account" when adding
  authors/speakers (:pr:`5553`)
- Include event label in email reminders (:issue:`5554`, :pr:`5556`,
  thanks :user:`omegak`)
- Include emails of submitters, speakers and authors in abstract/contribution
  Excel/CSV exports (:pr:`5565`)

Bugfixes
^^^^^^^^

- Fix meeting minutes being shown when they are expected to be hidden (:pr:`5475`)
- Force default locale when generating Book of Abstracts (:pr:`5477`)
- Fix width and height calculation when printing badges (:pr:`5479`)
- Parse escaped quotes (``&quot;``) in ckeditor output correctly (:pr:`5487`)
- Fix entering room name if room booking is enabled but has no locations (:pr:`5495`)
- Fix privacy information dropdown not opening on Safari (:pr:`5507`)
- Only let explicitly assigned reviewers review papers (:pr:`5527`)
- Never count participants from a registration forms with a fully hidden participant
  list for the total count on the participant page (:pr:`5532`)
- Fix "Session Legend" not working in all-days timetable view (:pr:`5539`)
- Fix exporting unlisted events via API (:pr:`5555`)

Internal Changes
^^^^^^^^^^^^^^^^

- Require at least Postgres 13 during new installations. This check can be
  forced on older Postgres versions (11+ should work), but we make no guarantees
  that nothing is broken (the latest version we test with is 12) (:pr:`5503`)
- Refactor service request email generation so plugins can override sender and
  reply-to addresses for these emails (:pr:`5501`)
- Deleting a session no longer leaves orphaned session blocks (:pr:`5533`,
  thanks :user:`omegak`)
- Indicate in the ``registration_deleted`` signal whether it's a permanent deletion
  from the database or just a soft-deletion (:pr:`5559`)


Version 3.2
-----------

*Released on August 25, 2022*

Major Features
^^^^^^^^^^^^^^

- The registration form frontend has been completely rewritten using modern web
  technology.
- Registrations can now have a retention period for the whole registration and
  individual fields, after which their data is permanently deleted.
- The participant list of an event can now use consent to determine whether a
  participant should be displayed, and its visibility can be different for the
  general public and other registered participants.
- An event can now have one or more privacy notices and it's possible to set the
  name and contact information of the "Data controller" (useful where GDPR or
  similar legislation applies).

Internationalization
^^^^^^^^^^^^^^^^^^^^

- New translation: German

Improvements
^^^^^^^^^^^^

- Add a new event management permission that grants access only to the abstracts
  module (:pr:`5212`)
- Add a link to quickly view the current stylesheet on the conference layout
  customization page (:issue:`5239`, :pr:`5259`)
- Add more powerful filters to "get next editable" and the list of editables
  (:issue:`5188`, :pr:`5224`, :pr:`5241`)
- Add the ability to create speaker-only menu entries for conferences (:issue:`5261`,
  :pr:`5268`)
- Highlight changed fields in notification emails about modified registrations
  (:issue:`5265`, :pr:`5269`)
- Add an option to send notifications of new abstract comments (:issue:`5266`, :pr:`5284`)
- Badge/poster templates can have additional images besides the background image
  (:pr:`5273`, thanks :user:`SegiNyn`)
- Add ability to add alerts to iCal exports (:issue:`5318`, :pr:`5320`, thanks
  :user:`PerilousApricot`)
- Show affiliations of submitters and authors in abstract/contribution lists and
  add an extra column with this information to Excel/CSV exports (:pr:`5330`)
- Add option to delete persons from the event if they have no roles or other ties
  to the event anymore (:issue:`5294`, :pr:`5313`)
- Allow events to be favorited (:issue:`1662`, :pr:`5338`, thanks :user:`Leats`)
- Include abstract content in CSV/Excel export if enabled in the abstract list
  (:issue:`5356`, :pr:`5372`, thanks :user:`rppt`)
- Add the ability to include an optional static javascript file when defining
  custom conference themes from within a plugin (:pr:`5414`, thanks :user:`brittyazel`)
- Add option to make the 'Affiliation' and 'Comment' fields mandatory in the account
  request form (:issue:`4819`, :pr:`5389`, thanks :user:`elsbethe`)
- Include tags in registrant API (:pr:`5441`)
- Subcontribution speakers can now be granted submission privileges in the event's
  protection settings (:issue:`2363`, :pr:`5444`)
- Registration forms can now require a CAPTCHA when the user is not logged in
  (:issue:`4698`, :pr:`5400`)
- Account creation now requires a CAPTCHA by default to prevent spam account creation
  (:issue:`4698`, :pr:`5446`)
- Add contribution's program code to revision's "Download ZIP" filename (:pr:`5449`)
- Add UI to manage series of events (:issue:`4048`, :pr:`5436`, thanks :user:`Leats`)
- Event series can now specify a title pattern to use when cloning an event in the
  series (:pr:`5456`)
- Insert new categories into the correct position if the list is already sorted (:pr:`5455`)
- Images can now be uploaded by pasting or dropping them into the editor for minutes
  or the event description (:pr:`5458`)
- Add JSON export for contribution details (:pr:`5460`)

Bugfixes
^^^^^^^^

- Fix selected state filters not showing up as selected in abstract list customization
  (:pr:`5363`)
- Do not propose an impossible date/time in the Room Booking module when accessing it
  shortly before midnight (:pr:`5371`)
- Do not fail when viewing an abstract that has been reviewed in a track which has
  been deleted in the meantime (:pr:`5386`)
- Fix error when editing a room's nonbookable periods (:pr:`5390`)
- Fix incorrect access check when directly accessing a registration form (:pr:`5406`)
- Fix error in rate limiter when using Redis with a UNIX socket connection (:issue:`5391`)
- Ensure that submitters with contribution edit privileges can only edit basic fields
  (:pr:`5425`)
- Do not return the whole contribution list when editing a contribution from elsewhere
  (:pr:`5425`)
- Fix session blocks not being sorted properly in a timetable PDF export when they
  have the same start time (:pr:`5426`)
- Fix printing badges containing text elements with malformed HTML (:pr:`5437`,
  thanks :user:`omegak`)
- Fix misleading start and end times for Poster contributions in the timetable HTTP API
  and the contributions placeholder in emails (:pr:`5443`)
- Do not mark persons as registered if the registration form has been deleted (:pr:`5448`)
- Fix error when a room owner who is not an admin edits their room (:pr:`5457`)

Internal Changes
^^^^^^^^^^^^^^^^

- When upgrading an existing instance, Postgres 11 or newer is required. The upgrade will
  fail on Postgres 9.6 (or 10).
- Add new ``regform-container-attrs`` template hook to pass additional (data-)attributes
  to the React registration form containers (:pr:`5271`)
- Add support for JavaScript plugin hooks to register objects or react components for use
  by JS code that's in the core (:pr:`5271`)
- Plugins can now define custom registration form fields (:pr:`5282`)
- Add :data:`EMAIL_BACKEND` configuration variable to support different email sending
  backends e.g. during development (:issue:`5375`, :pr:`5376`, thanks :user:`Moist-Cat`)
- Make model attrs to clone interceptable by plugins (:pr:`5403`, thanks :user:`omegak`)
- Add ``signal_query`` method in the ``IndicoBaseQuery`` class and the ``db_query``
  signal, allowing to intercept and modify queries by signal handlers (:pr:`4981`,
  thanks :user:`omegak`).
- Update WYSIWYG editor to CKEditor 5, resulting in a slightly different look for the
  editor controls and removal of some uncommon format options (:pr:`5345`)


----


Version 3.1.2
-------------

*Unreleased*

Bugfixes
^^^^^^^^

- Prevent access to a badge design of a deleted category or an event (:issue:`5329`,
  :pr:`5334`, thanks :user:`vasantvohra`)

Internal Changes
^^^^^^^^^^^^^^^^

- Let payment plugins ignore pending transactions if they are expired (:pr:`5357`)


Version 3.1.1
-------------

*Released on April 27, 2022*

Improvements
^^^^^^^^^^^^

- Prompt before leaving the event protection page without saving changes (:pr:`5222`)
- Add the ability to clone abstracts (:pr:`5217`)
- Add setting to allow submitters to edit their own contributions (:pr:`5213`)
- Update the editing state color scheme (:pr:`5236`)
- Include program codes in export API (:pr:`5246`)
- Add abstract rating scores grouped by track (:pr:`5298`)
- Allow uploading revisions when an editor hasn't been assigned (:pr:`5289`)

Bugfixes
^^^^^^^^

- Fix published editable files only being visible to users with access to the editing
  timeline (:pr:`5218`)
- Fix incorrect date in multi-day meeting date selector dropdown in certain timezones
  (:pr:`5223`)
- Remove excessive padding around category titles (:pr:`5225`)
- Fix error when exporting registrations to PDFs that contained certain invalid HTML-like
  sequences (:pr:`5233`)
- Restore logical order of registration list columns (:pr:`5240`)
- Fix a performance issue in the HTTP API when exporting events from a specific category
  while specifying a limit (only affected large databases) (:pr:`5260`)
- Correctly specify charset in iCalendar files attached to emails (:issue:`5228`,
  :pr:`5258`, thanks :user:`imranyusuff`)
- Fix very long map URLs breaking out of the event management settings box (:pr:`5275`)
- Fix missing abstract withdrawal notification (:pr:`5281`)
- Fix downloading files from editables without a published revision (:pr:`5290`)
- Do not mark participants with deleted/inactive registrations as registered in
  participant roles list (:pr:`5308`)
- Do not enforce personal token name uniqueness across different users (:pr:`5317`)
- Fix last modification date not updating when an abstract is edited (:pr:`5325`)
- Fix a bug with poster and badge printing in unlisted events (:pr:`5322`)

Internal Changes
^^^^^^^^^^^^^^^^

- Add ``category-sidebar`` template hook and blocks around category sidebar
  sections (:pr:`5237`, thanks :user:`omegak`)
- Add ``event.reminder.before_reminder_make_email`` signal (:pr:`5242`, thanks
  :user:`vasantvohra`)
- Add ``plugin.interceptable_function`` signal to intercept selected function
  calls (:pr:`5254`)


Version 3.1
-----------

*Released on January 11, 2022*

Major Features
^^^^^^^^^^^^^^

- Category managers now see a log of all changes made to their category in a
  category log (similar to the event log). This log includes information about
  all events being created, deleted or moved in the category (:issue:`2809`,
  :pr:`5029`)
- Besides letting everyone create events in a category or restricting it to
  specific users, categories now also support a moderation workflow which allows
  event managers to request moving an event to a category. Only once a category
  manager approves this request, the event is actually moved (:issue:`2057`, :pr:`5013`)
- Admins now have the option to enable "Unlisted events", which are events that
  are not (yet) assigned to a category. Such events are only accessible to its
  creator and other users who have been granted access explicitly, and do not
  show up in any category's event listing (:issue:`4294`, :issue:`5055`, :pr:`5023`,
  :pr:`5095`)

Improvements
^^^^^^^^^^^^

- Send event reminders as individual emails with the recipient in the To field
  instead of using BCC (:issue:`2318`, :pr:`5088`)
- Let event managers assign custom tags to registrations and filter the list
  of registrations by the presence or absence of specific tags (:issue:`4948`,
  :pr:`5091`)
- Allow importing registration invitations from a CSV file (:issue:`3673`, :pr:`5108`)
- Show event label on category overviews and in iCal event titles (:issue:`5140`,
  :pr:`5143`)
- Let event managers view the final timetable even while in draft mode (:issue:`5141`,
  :pr:`5145`)
- Add option to export role members as CSV (:issue:`5147`, :pr:`5156`)
- Include attachment checksums in API responses (:issue:`5084`, :pr:`5169`, thanks
  :user:`avivace`)
- iCalendar invites now render nicely in Outlook (:pr:`5178`)
- Envelope senders for emails can now be restricted to specific addresses/domains
  using the :data:`SMTP_ALLOWED_SENDERS` and :data:`SMTP_SENDER_FALLBACK` config
  settings (:issue:`4837`, :issue:`2224`, :issue:`1877`, :pr:`5179`)
- Allow filtering the contribution list based on whether any person (speaker or author)
  has registered for the event or not (:issue:`5192`, :pr:`5193`)
- Add background color option and layer order to badge/poster designer items (:pr:`5139`,
  thanks :user:`SegiNyn`)
- Allow external users in event/category ACLs (:pr:`5146`)

Bugfixes
^^^^^^^^

- Fix :data:`CUSTOM_COUNTRIES` not overriding names of existing countries (:pr:`5183`)
- Fix error dialog when submitting an invited abstract without being logger in (:pr:`5200`)
- Fix category picker search displaying deleted categories (:issue:`5197`, :pr:`5203`)
- Fix editing service API calls using the service token (:pr:`5170`)
- Fix excessive retries for Celery tasks with a retry wait time longer
  than 1 hour (:pr:`5172`)


----


Version 3.0.4
-------------

*Unreleased*

Improvements
^^^^^^^^^^^^

- Allow external users in event/category ACLs (:pr:`5146`)

Bugfixes
^^^^^^^^

- Fix editing service API calls using the service token (:pr:`5170`)
- Fix excessive retries for Celery tasks with a retry wait time longer
  than 1 hour (:pr:`5172`)


Version 3.0.3
-------------

*Released on October 28, 2021*

Security fixes
^^^^^^^^^^^^^^

- Protect authentication endpoints against CSRF login attacks (:pr:`5099`,
  thanks :user:`omegak`)

Improvements
^^^^^^^^^^^^

- Support TLS certificates for SMTP authentication (:pr:`5100`, thanks :user:`dweinholz`)
- Add CSV/Excel contribution list exports containing affiliations (:issue:`5114`, :pr:`5118`)
- Include program codes in contribution PDFs and spreadsheets (:pr:`5126`)
- Add an API for bulk-assigning contribution program codes programmatically (:issue:`5115`,
  :pr:`5120`)
- Add layout setting to show videoconferences on the main conference page (:pr:`5124`)

Bugfixes
^^^^^^^^

- Fix certain registration list filters (checkin status & state) being combined
  with OR instead of AND (:pr:`5101`)
- Fix translations not being taken into account in some places (:issue:`5073`, :pr:`5105`)
- Use correct/consistent field order for personal data fields in newly created
  registration forms
- Remove deleted registration forms from ACLs (:issue:`5130`, :pr:`5131`, thanks
  :user:`jbtwist`)

Internal Changes
^^^^^^^^^^^^^^^^

- Truncate file names to 150 characters to avoid hitting file system path limits
  (:pr:`5116`, thanks :user:`vasantvohra`)


Version 3.0.2
-------------

*Released on September 09, 2021*

Bugfixes
^^^^^^^^

- Fix JavaScript errors on the login page which caused problems when using multiple
  form-based login methods (e.g. LDAP and local Indico accounts)


Version 3.0.1
-------------

*Released on September 08, 2021*

Improvements
^^^^^^^^^^^^

- Allow filtering abstracts by custom fields having no value (:issue:`5033`, :pr:`5034`)
- Add support for syncing email addresses when logging in using external accounts
  (:pr:`5035`)
- Use more space-efficient QR code version in registration tickets (:pr:`5052`)
- Improve user experience when accessing an event restricted to registered participants
  while not logged in (:pr:`5053`)
- When searching external users, prefer results with a name in case of multiple matches
  with the same email address (:pr:`5066`)
- Show program codes in additional places (:pr:`5075`)
- Display localized country names (:issue:`5070`, :pr:`5076`)

Bugfixes
^^^^^^^^

- Show correct placeholders in date picker fields (:pr:`5022`)
- Correctly preselect the default currency when creating a registration form
- Do not notify registrants when a payment transaction is created in "pending" state
- Keep the order of multi-choice options in registration summary (:issue:`5020`, :pr:`5032`)
- Correctly handle relative URLs in PDF generation (:issue:`5042`, :pr:`5044`)
- Render markdown in track descriptions in PDF generation (:issue:`5043`, :pr:`5044`)
- Fix error when importing chairpersons from an existing event (:pr:`5047`)
- Fix broken timetable entry permalinks when query string args are present (:pr:`5049`)
- Do not show "Payments" event management menu entry for registration managers
  (:issue:`5072`)
- Replace some hardcoded date formats with locale-aware ones (:issue:`5059`, :pr:`5071`)
- Clone the scientific program description together with tracks (:pr:`5077`)
- Fix database error when importing registrations to an event that already contains a
  deleted registration form with registrations (:pr:`5078`)

Internal Changes
^^^^^^^^^^^^^^^^

- Add ``event.before_check_registration_email`` signal (:pr:`5021`, thanks :user:`omegak`)
- Do not strip image maps in places where HTML is allowed (:pr:`5026`, thanks
  :user:`bpedersen2`)
- Add ``event.registration.after_registration_form_clone`` signal (:pr:`5037`, thanks
  :user:`vasantvohra`)
- Add ``registration-invite-options`` template hook (:pr:`5045`, thanks :user:`vasantvohra`)
- Fix Typeahead widget not working with extra validators (:issue:`5048`, :pr:`5050`,
  thanks :user:`jbtwist`)


Version 3.0
-----------

*Released on July 16, 2021*

Major Features
^^^^^^^^^^^^^^

- Add system notices which inform administrators about important things such as security
  problems or outdated Python/Postgres versions. These notices are retrieved once a day
  without sending any data related to the Indico instance, but if necessary, this feature
  can be disabled by setting :data:`SYSTEM_NOTICES_URL` to ``None`` in ``indico.conf``
  (:pr:`5004`)
- It is now possible to use :ref:`SAML SSO <saml>` for authentication without the need for
  Shibboleth and Apache (:pr:`5014`)

Bugfixes
^^^^^^^^

- Fix formatting and datetime localization in various PDF exports and timetable tab headers
  (:pr:`5009`)
- Show lecture speakers as speakers instead of chairpersons on the participant roles page
  (:pr:`5008`)

Internal Changes
^^^^^^^^^^^^^^^^

- Signals previously exposed directly via ``signals.foo`` now need to be accessed using their
  explicit name, i.e. ``signals.core.foo`` (:pr:`5007`)
- Add ``category.extra_events`` signal (:pr:`5005`, thanks :user:`omegak`)


Version 3.0rc2
--------------

*Released on July 09, 2021*

Major Features
^^^^^^^^^^^^^^

- Add support for personal tokens. These tokens act like OAuth tokens, but are
  associated with a specific user and generated manually without the need of
  doing the OAuth flow. They can be used like API keys but with better granularity
  using the same scopes OAuth applications have, and a single user can have multiple
  tokens using various scopes. By default any user can create such tokens, but admins
  can restrict their creation.
  (:issue:`1934`, :pr:`4976`)

Improvements
^^^^^^^^^^^^

- Add abstract content to the abstract list customization options (:pr:`4968`)
- Add CLI option to create a series (:pr:`4969`)
- Users cannot submit multiple anonymous surveys anymore by logging out and in again
  (:issue:`4693`, :pr:`4970`)
- Improve reviewing state display for paper reviewers (:issue:`4979`, :pr:`4984`)
- Make it clearer if the contributions/timetable of a conference are still in draft mode
  (:issue:`4977`, :pr:`4986`)
- Add "send to speakers" option in event reminders (:issue:`4958`, :pr:`4966`, thanks
  :user:`Naveenaidu`)
- Allow displaying all events descending from a category (:issue:`4982`,
  :pr:`4983`, thanks :user:`omegak` and :user:`openprojects`).
- Add an option to allow non-judge conveners to update an abstract track (:pr:`4989`)

Bugfixes
^^^^^^^^

- Fix errors when importing events containing abstracts or event roles from a YAML dump
  (:pr:`4995`)
- Fix sorting abstract notification rules (:pr:`4998`)
- No longer silently fall back to the first event contact email address when sending
  registration emails where no explicit sender address has been configured (:issue:`4992`,
  :pr:`4996`, thanks :user:`vasantvohra`)
- Do not check for event access when using a registration link with a registration token
  (:issue:`4991`, :pr:`4997`, thanks :user:`vasantvohra`)


Version 3.0rc1
--------------

*Released on June 25, 2021*

Major Features
^^^^^^^^^^^^^^

- There is a new built-in search module which provides basic search functionality out
  of the box, and for more advanced needs (such as full text search in uploaded files)
  plugins can provide their own search functionality (e.g. using ElasticSearch).
  (:pr:`4841`)
- Categories may now contain both events and subcategories at the same time. During the
  upgrade to 3.0 event creation is automatically set to restricted in all categories
  containing subcategories in order to avoid any negative surprises which would suddenly
  allow random Indico users to create events in places where they couldn't do so previously.
  (:issue:`4679`, :pr:`4725`, :pr:`4757`)
- The OAuth provider module has been re-implemented based on a more modern
  library (authlib). Support for the somewhat insecure *implicit flow* has been
  removed in favor of the code-with-PKCE flow. Tokens are now stored more securely
  as a hash instead of plaintext. For a given user/app/scope combination, only a
  certain amount of tokens are stored; once the limit has been reached older tokens
  will be discarded. The OAuth provider now exposes its metadata via a well-known
  URI (RFC 8414) and also has endpoints to introspect or revoke a token. (:issue:`4685`,
  :pr:`4798`)
- User profile pictures (avatars) are now shown in many more places throughout Indico,
  such as user search results, meeting participant lists and reviewing timelines.
  (:issue:`4625`, :pr:`4747`, :pr:`4939`)

Internationalization
^^^^^^^^^^^^^^^^^^^^

- New locale: English (United States)
- New translation: Turkish

Improvements
^^^^^^^^^^^^

- Use a more modern search dialog when searching for users (:issue:`4674`, :pr:`4743`)
- Add an option to refresh event person data from the underlying user when cloning an
  event (:issue:`4750`, :pr:`4760`)
- Add options for attaching iCal files to complete registration and event reminder
  emails (:issue:`1158`, :pr:`4780`)
- Use the new token-based URLs instead of API keys for persistent ical links and replace
  the calendar link widgets in category, event, session and contribution views with the
  more modern ones used in dashboard (:issue:`4776`, :pr:`4801`)
- Add an option to export editables to JSON (:issue:`4767`, :pr:`4810`)
- Add an option to export paper peer reviewing data to JSON (:issue:`4767`, :pr:`4818`)
- Passwords are now checked against a list of breached passwords ("Have I Been Pwned")
  in a secure and anonymous way that does not disclose any data. If a user logs in with
  an insecure password, they are forced to change it before they can continue using Indico
  (:pr:`4817`)
- Failed login attempts now trigger rate limiting to prevent brute-force attacks
  (:issue:`1550`, :pr:`4817`)
- Allow filtering the "Participant Roles" page by users who have not registered for the event
  (:issue:`4763`, :pr:`4822`)
- iCalendar exports now include contact data, event logo URL and, when exporting
  sessions/contributions, the UID of the related event. Also, only non-empty fields
  are exported. (:issue:`4785`, :issue:`4586`, :issue:`4587`, :issue:`4791`,
  :pr:`4820`)
- Allow adding groups/roles as "authorized abstract submitters" (:pr:`4834`)
- Direct links to (sub-)contributions in meetings using the URLs usually meant for
  conferences now redirect to the meeting view page (:pr:`4847`)
- Use a more compact setup QR code for the mobile *Indico check-in* app; the latest version of
  the app is now required. (:pr:`4844`)
- Contribution duration fields now use a widget similar to the time picker that makes selecting
  durations easier. (:issue:`2462`, :pr:`4873`)
- Add new meeting themes that show sequential numbers instead of start times for contributions
  (:pr:`4899`)
- Remove the very outdated "Compact style" theme (it's still available via the ``themes_legacy``
  plugin) (:issue:`4900`, :pr:`4899`)
- Support cloning surveys when cloning events (:issue:`2045`, :pr:`4910`)
- Show external contribution references in conferences (:issue:`4928`, :pr:`4933`)
- Allow changing the rating scale in abstract/paper reviewing even after reviewing started (:pr:`4942`)
- Allow blacklisting email addresses for user registrations (:issue:`4644`, :pr:`4946`)

Bugfixes
^^^^^^^^

- Take registrations of users who are only members of a custom event role into account on the
  "Participant Roles" page (:pr:`4822`)
- Fail gracefully during registration import when two rows have different emails that belong
  to the same user (:pr:`4823`)
- Restore the ability to see who's inheriting access from a parent object (:pr:`4833`)
- Fix misleading message when cancelling a booking that already started and has past
  occurrences that won't be cancelled (:issue:`4719`, :pr:`4861`)
- Correctly count line breaks in length-limited abstracts (:pr:`4918`)
- Fix error when trying to access subcontributions while event is in draft mode
- Update the user link in registrations when merging two users (:pr:`4936`)
- Fix error when exporting a conference timetable PDF with the option "Print abstract content of all
  contributions" and one of the abstracts is too big to fit in a page (:issue:`4881`, :pr:`4955`)
- Emails sent via the Editing module are now logged to the event log (:pr:`4960`)
- Fix error when importing event notes from another event while the target event already
  has a deleted note (:pr:`4959`)

Internal Changes
^^^^^^^^^^^^^^^^

- Require Python 3.9 - older Python versions (especially Python 2.7) are **no longer supported**
- ``confId`` has been changed to ``event_id`` and the corresponding URL path segments
  now enforce numeric data (and thus pass the id as a number instead of string)
- ``CACHE_BACKEND`` has been removed; Indico now always uses Redis for caching
- The integration with flower (celery monitoring tool) has been removed as it was not widely used,
  did not provide much benefit, and it is no longer compatible with the latest Celery version
- ``session.user`` now returns the user related to the current request, regardless of whether
  it's coming from OAuth, a signed url or the actual session (:pr:`4803`)
- Add a new ``check_password_secure`` signal that can be used to implement additional password
  security checks (:pr:`4817`)
- Add an endpoint to let external applications stage the creation of an event with some data to be
  pre-filled when the user then opens the link returned by that endpoint (:pr:`4628`, thanks
  :user:`adl1995`)


----


Version 2.3.6
-------------

*Unreleased*

Bugfixes
^^^^^^^^

- None so far :)


Version 2.3.5
-------------

*Released on May 11, 2021*

Security fixes
^^^^^^^^^^^^^^

- Fix XSS vulnerabilities in the category picker (via category titles), location widget (via room and
  venue names defined by an Indico administrator) and the "Indico Weeks View" timetable theme (via
  contribution/break titles defined by an event organizer). As neither of these objects can be created
  by untrusted users (on a properly configured instance) we consider the severity of this vulnerability
  "minor" (:pr:`4897`)

Internationalization
^^^^^^^^^^^^^^^^^^^^

- New translation: Polish
- New translation: Mongolian

Improvements
^^^^^^^^^^^^

- Add an option to not disclose the names of editors and commenters to submitters in the
  Paper Editing module (:issue:`4829`, :pr:`4865`)

Bugfixes
^^^^^^^^

- Do not show soft-deleted long-lasting events in category calendar (:pr:`4824`)
- Do not show management-related links in editing hybrid view unless the user has
  access to them (:pr:`4830`)
- Fix error when assigning paper reviewer roles with notifications enabled and one
  of the reviewing types disabled (:pr:`4838`)
- Fix viewing timetable entries if you cannot access the event but a specific session
  inside it (:pr:`4857`)
- Fix viewing contributions if you cannot access the event but have explicit access to
  the contribution (:pr:`4860`)
- Hide registration menu item if you cannot access the event and registrations are not
  exempt from event access checks (:pr:`4860`)
- Fix inadvertently deleting a file uploaded during the "make changes" Editing action,
  resulting in the revision sometimes still referencing the file even though it has been
  deleted from storage (:pr:`4866`)
- Fix sorting abstracts by date (:pr:`4877`)

Internal Changes
^^^^^^^^^^^^^^^^

- Add ``before_notification_send`` signal (:pr:`4874`, thanks :user:`omegak`)


Version 2.3.4
-------------

*Released on March 11, 2021*

Security fixes
^^^^^^^^^^^^^^

- Fix some open redirects which could help making harmful URLs look more trustworthy by linking
  to Indico and having it redirect the user to a malicious site (:issue:`4814`, :pr:`4815`)
- The :data:`BASE_URL` is now always enforced and requests whose Host header does not match
  are rejected. This prevents malicious actors from tricking Indico into sending e.g. a
  password reset link to a user that points to a host controlled by the attacker instead of
  the actual Indico host (:pr:`4815`)

.. note::

    If the webserver is already configured to enforce a canonical host name and redirects or
    rejects such requests, this cannot be exploited. Additionally, exploiting this problem requires
    user interaction: they would need to click on a password reset link which they never requested,
    and which points to a domain that does not match the one where Indico is running.

Improvements
^^^^^^^^^^^^

- Fail more gracefully is a user has an invalid locale set and fall back to the default
  locale or English in case the default locale is invalid as well
- Log an error if the configured default locale does not exist
- Add ID-1 page size for badge printing (:pr:`4774`, thanks :user:`omegak`)
- Allow managers to specify a reason when rejecting registrants and add a new placeholder
  for the rejection reason when emailing registrants (:pr:`4769`, thanks :user:`vasantvohra`)

Bugfixes
^^^^^^^^

- Fix the "Videoconference Rooms" page in conference events when there are any VC rooms
  attached but the corresponding plugin is no longer installed
- Fix deleting events which have a videoconference room attached which has its VC plugin
  no longer installed
- Do not auto-redirect to SSO when an MS office user agent is detected (:issue:`4720`,
  :pr:`4731`)
- Allow Editing team to view editables of unpublished contributions (:issue:`4811`, :pr:`4812`)

Internal Changes
^^^^^^^^^^^^^^^^

- Also trigger the ``ical-export`` metadata signal when exporting events for a whole category
- Add ``primary_email_changed`` signal (:pr:`4802`, thanks :user:`openprojects`)


Version 2.3.3
-------------

*Released on January 25, 2021*

Security fixes
^^^^^^^^^^^^^^

- JSON locale data for invalid locales is no longer cached on disk; instead a 404 error is
  triggered. This avoids creating small files in the cache folder for each invalid locale
  that is requested. (:pr:`4766`)

Internationalization
^^^^^^^^^^^^^^^^^^^^

- New translation: Ukrainian

Improvements
^^^^^^^^^^^^

- Add a new "Until approved" option for a registration form's "Modification allowed"
  setting (:pr:`4740`, thanks :user:`vasantvohra`)
- Show last login time in dashboard (:pr:`4735`, thanks :user:`vasantvohra`)
- Allow Markdown in the "Message for complete registrations" option of a registration
  form (:pr:`4741`)
- Improve video conference linking dropdown for contributions/sessions (hide unscheduled,
  show start time) (:pr:`4753`)
- Show timetable filter button in conferences with a meeting-like timetable

Bugfixes
^^^^^^^^

- Fix error when converting malformed HTML links to LaTeX
- Hide inactive contribution/abstract fields in submit/edit forms (:pr:`4755`)
- Fix adding registrants to a session ACL

Internal Changes
^^^^^^^^^^^^^^^^

- Videoconference plugins may now display a custom message for the prompt when deleting
  a videoconference room (:pr:`4733`)
- Videoconference plugins may now override the behavior when cloning an event with
  attached videoconference rooms (:pr:`4732`)


Version 2.3.2
-------------

*Released on November 30, 2020*

Improvements
^^^^^^^^^^^^

- Disable title field by default in new registration forms (:issue:`4688`, :pr:`4692`)
- Add gender-neutral "Mx" title (:issue:`4688`, :pr:`4692`)
- Add contributions placeholder for emails (:pr:`4716`, thanks :user:`bpedersen2`)
- Show program codes in contribution list (:pr:`4713`)
- Display the target URL of link materials if the user can access them (:issue:`2599`,
  :pr:`4718`)
- Show the revision number for all revisions in the Editing timeline (:pr:`4708`)

Bugfixes
^^^^^^^^

- Only consider actual speakers in the "has registered speakers" contribution list filter
  (:pr:`4712`, thanks :user:`bpedersen2`)
- Correctly filter events in "Sync with your calendar" links (this fix only applies to newly
  generated links) (:pr:`4717`)
- Correctly grant access to attachments inside public sessions/contribs even if the event
  is more restricted (:pr:`4721`)
- Fix missing filename pattern check when suggesting files from Paper Peer Reviewing to submit
  for Editing (:pr:`4715`)
- Fix filename pattern check in Editing when a filename contains dots (:pr:`4715`)
- Require explicit admin override (or being whitelisted) to override blockings (:pr:`4706`)
- Clone custom abstract/contribution fields when cloning abstract settings (:pr:`4724`,
  thanks :user:`bpedersen2`)
- Fix error when rescheduling a survey that already has submissions (:issue:`4730`)


Version 2.3.1
-------------

*Released on October 27, 2020*

Security fixes
^^^^^^^^^^^^^^
- Fix potential data leakage between OAuth-authenticated and unauthenticated HTTP API requests
  for the same resource (:pr:`4663`)

.. note::

    Due to OAuth access to the HTTP API having been broken until this version, we do not
    believe this was actually exploitable on any Indico instance. In addition, only Indico
    administrators can create OAuth applications, so regardless of the bug there is no risk
    for any instance which does not have OAuth applications with the ``read:legacy_api``
    scope.

Improvements
^^^^^^^^^^^^

- Generate material packages in a background task to avoid timeouts or using excessive
  amounts of disk space in case of people submitting several times (:pr:`4630`)
- Add new :data:`EXPERIMENTAL_EDITING_SERVICE` setting to enable extending an event's Editing
  workflow through an `OpenReferee server <https://github.com/indico/openreferee/>`_ (:pr:`4659`)

Bugfixes
^^^^^^^^

- Only show the warning about draft mode in a conference if it actually has any
  contributions or timetable entries
- Do not show incorrect modification deadline in abstract management area if no
  such deadline has been set (:pr:`4650`)
- Fix layout problem when minutes contain overly large embedded images (:issue:`4653`,
  :pr:`4654`)
- Prevent pending registrations from being marked as checked-in (:pr:`4646`, thanks
  :user:`omegak`)
- Fix OAuth access to HTTP API (:pr:`4663`)
- Fix ICS export of events with draft timetable and contribution detail level
  (:pr:`4666`)
- Fix paper revision submission field being displayed for judges/reviewers (:pr:`4667`)
- Fix managers not being able to submit paper revisions on behalf of the user (:pr:`4667`)

Internal Changes
^^^^^^^^^^^^^^^^

- Add ``registration_form_wtform_created`` signal and send form data in
  ``registration_created`` and ``registration_updated`` signals (:pr:`4642`,
  thanks :user:`omegak`)
- Add ``logged_in`` signal


Version 2.3
-----------

*Released on September 14, 2020*

.. note::

    We also published a `blog post <https://getindico.io/indico/update/release/milestone/2020/07/22/indico-2-3-news.html>`_
    summarizing the most relevant changes for end users.

Major Features
^^^^^^^^^^^^^^

- Add category roles, which are similar to local groups but within the
  scope of a category and its subcategories. They can be used for assigning
  permissions in any of these categories and events within such categories.
- Events marked as "Invisible" are now hidden from the category's event list
  for everyone except managers (:issue:`4419`, thanks :user:`openprojects`)
- Introduce profile picture, which is for now only visible on the user dashboard
  (:issue:`4431`, thanks :user:`omegak`)
- Registrants can now be added to event ACLs. This can be used to easily restrict
  parts of an event to registered participants. If registration is open and a registration
  form is in the ACL, people will be able to access the registration form even if they
  would otherwise not have access to the event itself. It is also possible to restrict
  individual event materials and custom page/link menu items to registered participants.
  (:issue:`4477`, :issue:`4528`, :issue:`4505`, :issue:`4507`)
- Add a new Editing module for papers, slides and posters which provides a workflow
  for having a team review the layout/formatting of such proceedings and then publish
  the final version on the page of the corresponding contribution. The Editing module
  can also be connected to an external microservice to handle more advanced workflows
  beyond what is supported natively by Indico.

Internationalization
^^^^^^^^^^^^^^^^^^^^

- New translation: Chinese (Simplified)

Improvements
^^^^^^^^^^^^

- Sort survey list by title (:issue:`3802`)
- Hide "External IDs" field if none are defined (:issue:`3857`)
- Add LaTeX source export for book of abstracts (:issue:`4035`,
  thanks :user:`bpedersen2`)
- Tracks can now be categorized in track groups (:issue:`4052`)
- Program codes for sessions, session blocks, contributions and
  subcontributions can now be auto-generated (:issue:`4026`)
- Add draft mode for the contribution list of conference events
  which hides pages like the contribution list and timetable until
  the event organizers publish the contribution list. (:issue:`4095`)
- Add ICS export for information in the user dashboard (:issue:`4057`)
- Allow data syncing with multipass providers which do not support
  refreshing identity information
- Show more verbose error when email validation fails during event
  registration (:issue:`4177`)
- Add link to external map in room details view (:issue:`4146`)
- Allow up to 9 digits (instead of 6) before the decimal point in
  registration fees
- Add button to booking details modal to copy direct link (:issue:`4230`)
- Do not require new room manager approval when simply shortening a booking
  (:issue:`4214`)
- Make root category description/title customizable using the normal
  category settings form (:issue:`4231`)
- Added new :data:`LOCAL_GROUPS` setting that can be used to fully disable
  local groups (:issue:`4260`)
- Log bulk event category changes in the event log (:issue:`4241`)
- Add CLI commands to block and unblock users (:issue:`3845`)
- Show warning when trying to merge a blocked user (:issue:`3845`)
- Allow importing event role members from a CSV file (:issue:`4301`)
- Allow optional comment when accepting a pre-booking (:issue:`4086`)
- Log event restores in event log (:issue:`4309`)
- Warn about cancelling/rejecting whole recurring bookings instead of just
  specific occurrences (:issue:`4092`)
- Add "quick cancel" link to room booking reminder emails (:issue:`4324`)
- Add visual information and filtering options for participants'
  registration status to the contribution list (:issue:`4318`)
- Add warning when accepting a pre-booking in case there are
  concurrent bookings (:issue:`4129`)
- Add event logging to opening/closing registration forms, approval/rejection of
  registrations, and updates to event layout (:issue:`4360`,
  thanks :user:`giusedb` & :user:`omegak`)
- Add category navigation dialog on category display page (:issue:`4282`,
  thanks :user:`omegak`)
- Add UI for admins to block/unblock users (:issue:`3243`)
- Show labels indicating whether a user is an admin, blocked or soft-deleted
  (:issue:`4363`)
- Add map URL to events, allowing also to override room map URL (:issue:`4402`,
  thanks :user:`omegak`)
- Use custom time picker for time input fields taking into account the 12h/24h
  format of the user's locale (:issue:`4399`)
- Refactor the room edit modal to a tabbed layout and improve error
  handling (:issue:`4408`)
- Preserve non-ascii characters in file names (:issue:`4465`)
- Allow resetting moderation state from registration management view
  (:issue:`4498`, thanks :user:`omegak`)
- Allow filtering event log by related entries (:issue:`4503`, thanks
  :user:`omegak`)
- Do not automatically show the browser's print dialog in a meeting's print
  view (:issue:`4513`)
- Add "Add myself" button to person list fields (e.g. for abstract authors)
  (:issue:`4411`, thanks :user:`jgrigera`)
- Subcontributions can now be managed from the meeting display view (:issue:`2679`,
  :pr:`4520`)
- Add CfA setting to control whether authors can edit abstracts (:issue:`3431`)
- Add CfA setting to control whether only speakers or also authors should
  get submission rights once the abstract gets accepted (:issue:`3431`)
- Show the Indico version in the footer again (:issue:`4558`)
- Event managers can upload a custom Book of Abstract PDF (:issue:`3039`,
  :pr:`4577`)
- Display each news item on a separate page instead of together with all the
  other news items (:pr:`4587`)
- Allow registrants to withdraw their application (:issue:`2715`, :pr:`4585`,
  thanks :user:`brabemi` & :user:`omegak`)
- Allow choosing a default badge in categories (:pr:`4574`, thanks
  :user:`omegak`)
- Display event labels on the user's dashboard as well (:pr:`4592`)
- Event modules can now be imported from another event (:issue:`4518`, thanks :user:`meluru`)
- Event modules can now be imported from another event (:issue:`4518`, :pr:`4533`,
  thanks :user:`meluru`)
- Include the event keywords in the event API data (:issue:`4598`, :pr:`4599`,
  thanks :user:`chernals`)
- Allow registrants to check details for non-active registrations and prevent
  them from registering twice with the same registration form (:issue:`4594`,
  :pr:`4595`, thanks :user:`omegak`)
- Add a new :data:`CUSTOM_LANGUAGES` setting to ``indico.conf`` to override the
  name/territory of a language or disable it altogether (:pr:`4620`)

Bugfixes
^^^^^^^^

- Hide Book of Abstracts menu item if LaTeX is disabled and no custom Book
  of Abstracts has been uploaded
- Use a more consistent order when cloning the timetable (:issue:`4227`)
- Do not show unrelated rooms with similar names when booking room from an
  event (:issue:`4089`)
- Stop icons from overlapping in the datetime widget (:issue:`4342`)
- Fix alignment of materials in events (:issue:`4344`)
- Fix misleading wording in protection info message (:issue:`4410`)
- Allow guests to access public notes (:issue:`4436`)
- Allow width of weekly event overview table to adjust to window
  size (:issue:`4429`)
- Fix whitespace before punctuation in Book of Abstracts (:pr:`4604`)
- Fix empty entries in corresponding authors (:pr:`4604`)
- Actually prevent users from editing registrations if modification is
  disabled
- Handle LaTeX images with broken redirects (:pr:`4623`, thanks :user:`bcc`)

Internal Changes
^^^^^^^^^^^^^^^^

- Make React and SemanticUI usable everywhere (:issue:`3955`)
- Add ``before-regform`` template hook (:issue:`4171`, thanks :user:`giusedb`)
- Add ``registrations`` kwarg to the ``event.designer.print_badge_template``
  signal (:issue:`4297`, thanks :user:`giusedb`)
- Add ``registration_form_edited`` signal (:issue:`4421`, thanks :user:`omegak`)
- Make PyIntEnum freeze enums in Alembic revisions (:issue:`4425`, thanks
  :user:`omegak`)
- Add ``before-registration-summary`` template hook (:issue:`4495`, thanks
  :user:`omegak`)
- Add ``extra-registration-actions`` template hook (:issue:`4500`, thanks
  :user:`omegak`)
- Add ``event-management-after-title`` template hook (:issue:`4504`, thanks
  :user:`meluru`)
- Save registration id in related event log entries (:issue:`4503`, thanks
  :user:`omegak`)
- Add ``before-registration-actions`` template hook (:issue:`4524`, thanks
  :user:`omegak`)
- Add ``LinkedDate`` and ``DateRange`` form field validators (:issue:`4535`,
  thanks :user:`omegak`)
- Add ``extra-regform-settings`` template hook (:issue:`4553`, thanks
  :user:`meluru`)
- Add ``filter_selectable_badges`` signal (:issue:`4557`, thanks :user:`omegak`)
- Add user ID in every log record logged in a request context (:issue:`4570`,
  thanks :user:`omegak`)
- Add ``extra-registration-settings`` template hook (:pr:`4596`, thanks
  :user:`meluru`)
- Allow extending polymorphic models in plugins (:pr:`4608`, thanks
  :user:`omegak`)
- Wrap registration form AngularJS directive in jinja block for more easily
  overriding arguments passed to the app in plugins (:pr:`4624`, thanks
  :user:`omegak`)


----


Version 2.2.9
-------------

*Unreleased*

Bugfixes
^^^^^^^^

- Fix error when building LaTeX PDFs if the temporary event logo path contained
  an underscore (:issue:`4521`)
- Disallow storing invalid timezones in user settings and reduce risk of sending
  wrong timezone names when people automatically translate their UI (:issue:`4529`)


Version 2.2.8
-------------

*Released on April 08, 2020*

Security fixes
^^^^^^^^^^^^^^

- Update `bleach <https://github.com/mozilla/bleach>`_ to fix a regular expression
  denial of service vulnerability
- Update `Pillow <https://github.com/python-pillow/Pillow>`_ to fix a buffer overflow
  vulnerability


Version 2.2.7
-------------

*Released on March 23, 2020*

Improvements
^^^^^^^^^^^^

- Add support for event labels to indicate e.g. postponed or cancelled
  events (:issue:`3199`)

Bugfixes
^^^^^^^^

- Allow slashes in roomName export API
- Show names instead of IDs of local groups in ACLs (:issue:`3700`)


Version 2.2.6
-------------

*Released on February 27, 2020*

Bugfixes
^^^^^^^^

- Fix some email fields (error report contact, agreement cc address) being
  required even though they should be optional
- Avoid browsers prefilling stored passwords in togglable password fields
  such as the event access key
- Make sure that tickets are not attached to emails sent to registrants for whom
  tickets are blocked (:issue:`4242`)
- Fix event access key prompt not showing when accessing an attachment link
  (:issue:`4255`)
- Include event title in OpenGraph metadata (:issue:`4288`)
- Fix error when viewing abstract with reviews that have no scores
- Update requests and pin idna to avoid installing incompatible dependency versions
  (:issue:`4327`)


Version 2.2.5
-------------

*Released on December 06, 2019*

Improvements
^^^^^^^^^^^^

- Sort posters in timetable PDF export by board number (:issue:`4147`, thanks
  :user:`bpedersen2`)
- Use lat/lng field order instead of lng/lat when editing rooms (:issue:`4150`,
  thanks :user:`bpedersen2`)
- Add additional fields to the contribution csv/xlsx export (authors and board
  number) (:issue:`4148`, thanks :user:`bpedersen2`)

Bugfixes
^^^^^^^^

- Update the Pillow library to 6.2.1. This fixes an issue where some malformed images
  could result in high memory usage or slow processing.
- Truncate long speaker names in the timetable instead of hiding them (:issue:`4110`)
- Fix an issue causing errors when using translations for languages with no plural
  forms (like Chinese).
- Fix creating rooms without touching the longitude/latitude fields (:issue:`4115`)
- Fix error in HTTP API when Basic auth headers are present (:issue:`4123`,
  thanks :user:`uxmaster`)
- Fix incorrect font size in some room booking dropdowns (:issue:`4156`)
- Add missing email validation in some places (:issue:`4158`)
- Reject requests containing NUL bytes in the POST data (:issue:`4159`)
- Fix truncated timetable PDF when using "Print each session on a separate page" in
  an event where the last timetable entry of the day is a top-level contribution
  or break (:issue:`4134`, thanks :user:`bpedersen2`)
- Only show public contribution fields in PDF exports (:issue:`4165`)
- Allow single arrival/departure date in accommodation field (:issue:`4164`,
  thanks :user:`bpedersen2`)


Version 2.2.4
-------------

*Released on October 16, 2019*

Security fixes
^^^^^^^^^^^^^^

- Fix more places where LaTeX input was not correctly sanitized. While the biggest
  security impact (reading local files) has already been mitigated when fixing the
  initial vulnerability in the previous release, it is still strongly recommended
  to update.


Version 2.2.3
-------------

*Released on October 08, 2019*

Security fixes
^^^^^^^^^^^^^^

- Strip ``@``, ``+``, ``-`` and ``=`` from the beginning of strings when exporting
  CSV files to avoid `security issues <https://www.owasp.org/index.php/CSV_Injection>`_
  when opening the CSV file in Excel
- Use 027 instead of 000 umask when temporarily changing it to get the current umask
- Fix LaTeX sanitization to prevent malicious users from running unsafe LaTeX commands
  through specially crafted abstracts or contribution descriptions, which could lead to
  the disclosure of local file contents

Improvements
^^^^^^^^^^^^

- Improve room booking interface on small-screen devices (:issue:`4013`)
- Add user preference for room owners/manager to select if they want to
  receive notification emails for their rooms (:issue:`4096`, :issue:`4098`)
- Show family name field first in user search dialog (:issue:`4099`)
- Make date headers clickable in room booking calendar (:issue:`4099`)
- Show times in room booking log entries (:issue:`4099`)
- Support disabling server-side LaTeX altogether and hide anything that
  requires it (such as contribution PDF export or the Book of Abstracts).
  **LaTeX is now disabled by default, unless the** :data:`XELATEX_PATH`
  **is explicitly set in** ``indico.conf``.


Bugfixes
^^^^^^^^

- Remove 30s timeout from dropzone file uploads
- Fix bug affecting room booking from an event in another timezone (:issue:`4072`)
- Fix error when commenting on papers (:issue:`4081`)
- Fix performance issue in conferences with public registration count and a
  high amount of registrations
- Fix confirmation prompt when disabling conference menu customizations
  (:issue:`4085`)
- Fix incorrect days shown as weekend in room booking for some locales
- Fix ACL entries referencing event roles from the old event when cloning an
  event with event roles in the ACL. Run ``indico maint fix-event-role-acls``
  after updating to fix any affected ACLs (:issue:`4090`)
- Fix validation issues in coordinates fields when editing rooms (:issue:`4103`)


Version 2.2.2
-------------

*Released on August 23, 2019*

Bugfixes
^^^^^^^^

- Remove dependency on ``pyatom``, which has vanished from PyPI


Version 2.2.1
-------------

*Released on August 16, 2019*

Improvements
^^^^^^^^^^^^

- Make list of event room bookings sortable (:issue:`4022`)
- Log when a booking is split during editing (:issue:`4031`)
- Improve "Book" button in multi-day events (:issue:`4021`)

Bugfixes
^^^^^^^^

- Add missing slash to the ``template_prefix`` of the ``designer`` module
- Always use HH:MM time format in book-from-event link
- Fix timetable theme when set to "indico weeks view" before 2.2 (:issue:`4027`)
- Avoid flickering of booking edit details tooltip
- Fix outdated browser check on iOS (:issue:`4033`)


Version 2.2
-----------

*Released on August 06, 2019*

Major Changes
^^^^^^^^^^^^^

- ⚠️ **Drop support for Internet Explorer 11 and other outdated or
  discontinued browser versions.** Indico shows a warning message
  when accessed using such a browser. The latest list of supported
  browsers can be found `in the README on GitHub <https://github.com/indico/indico#browser-support>`_,
  but generally Indico now supports the last two versions of each major
  browser (determined at release time), plus the current Firefox ESR.
- Rewrite the room booking frontend to be more straightforward and
  user-friendly. Check `our blog for details <https://getindico.io/indico/update/release/milestone/2019/02/22/indico-2-2-news.html>`_.

Improvements
^^^^^^^^^^^^

- Rework the event log viewer to be more responsive and not freeze the
  whole browser when there are thousands of log entries
- Add shortcut to next upcoming event in a category (:issue:`3388`)
- Make registration period display less confusing (:issue:`3359`)
- Add edit button to custom conference pages (:issue:`3284`)
- Support markdown in survey questions (:issue:`3366`)
- Improve event list in case of long event titles (:issue:`3607`,
  thanks :user:`nop33`)
- Include event page title in the page's ``<title>`` (:issue:`3285`,
  thanks :user:`bpedersen2`)
- Add option to include subcategories in upcoming events (:issue:`3449`)
- Allow event managers to override the name format used in the event
  (:issue:`2455`)
- Add option to not clone venue/room of an event
- Show territory/country next to the language name (:issue:`3968`)
- Add more sorting options to book of abstracts (:issue:`3429`, thanks
  :user:`bpedersen2`)
- Add more formatting options to book of abstracts (:issue:`3335`, thanks
  :user:`bpedersen2`)
- Improve message when the call for abstracts is scheduled to open but
  hasn't started yet
- Make link color handling for LaTeX pdfs configurable (:issue:`3283`,
  thanks :user:`bpedersen2`)
- Preserve displayed order in contribution exports that do not apply
  any specific sorting (:issue:`4005`)
- Add author list button to list of papers (:issue:`3978`)

Bugfixes
^^^^^^^^

- Fix incorrect order of session blocks inside timetable (:issue:`2999`)
- Add missing email validation to contribution CSV import (:issue:`3568`,
  thanks :user:`Kush22`)
- Do not show border after last item in badge designer toolbar
  (:issue:`3607`, thanks :user:`nop33`)
- Correctly align centered footer links (:issue:`3599`, thanks :user:`nop33`)
- Fix top/right alignment of session bar in event display view (:issue:`3599`,
  thanks :user:`nop33`)
- Fix error when trying to create a user with a mixed-case email
  address in the admin area
- Fix event import if a user in the exported data has multiple email
  addresses and they match different users
- Fix paper reviewers getting notifications even if their type of reviewing
  has been disabled (:issue:`3852`)
- Correctly handle merging users in the paper reviewing module (:issue:`3895`)
- Show correct number of registrations in management area (:issue:`3935`)
- Fix sorting book of abstracts by board number (:issue:`3429`, thanks
  :user:`bpedersen2`)
- Enforce survey submission limit (:issue:`3256`)
- Do not show "Mark as paid" button and checkout link while a transaction
  is pending (:issue:`3361`, thanks :user:`driehle`)
- Fix 404 error on custom conference pages that do not have any ascii chars
  in the title (:issue:`3998`)
- Do not show pending registrants in public participant lists (:issue:`4017`)

Internal Changes
^^^^^^^^^^^^^^^^

- Use webpack to build static assets
- Add React+Redux for new frontend modules
- Enable modern ES201x features


----


Version 2.1.11
--------------

*Released on October 16, 2019*

Security fixes
^^^^^^^^^^^^^^

- Fix more places where LaTeX input was not correctly sanitized. While the biggest
  security impact (reading local files) has already been mitigated when fixing the
  initial vulnerability in the previous release, it is still strongly recommended
  to update.


Version 2.1.10
--------------

*Released on October 08, 2019*

Security fixes
^^^^^^^^^^^^^^

- Strip ``@``, ``+``, ``-`` and ``=`` from the beginning of strings when exporting
  CSV files to avoid `security issues <https://www.owasp.org/index.php/CSV_Injection>`_
  when opening the CSV file in Excel
- Use 027 instead of 000 umask when temporarily changing it to get the current umask
- Fix LaTeX sanitization to prevent malicious users from running unsafe LaTeX commands
  through specially crafted abstracts or contribution descriptions, which could lead to
  the disclosure of local file contents


Version 2.1.9
-------------

*Released on August 26, 2019*

Bugfixes
^^^^^^^^

- Fix bug in calendar view, due to timezones (:issue:`3903`)
- Remove dependency on ``pyatom``, which has vanished from PyPI (:issue:`4045`)


Version 2.1.8
-------------

*Released on March 12, 2019*

Improvements
^^^^^^^^^^^^

- Add A6 to page size options (:issue:`3793`)

Bugfixes
^^^^^^^^

- Fix celery/redis dependency issue (:issue:`3809`)


Version 2.1.7
-------------

*Released on January 24, 2019*

Improvements
^^^^^^^^^^^^

- Add setting for the default contribution duration of an event
  (:issue:`3446`)
- Add option to copy abstract attachments to contributions when
  accepting them (:issue:`3732`)

Bugfixes
^^^^^^^^

- Really fix the oauthlib conflict (was still breaking in some cases)


Version 2.1.6
-------------

*Released on January 15, 2019*

Bugfixes
^^^^^^^^

- Allow adding external users as speakers/chairpersons (:issue:`3562`)
- Allow adding external users to event ACLs (:issue:`3562`)
- Pin requests-oauthlib version to avoid dependency conflict


Version 2.1.5
-------------

*Released on December 06, 2018*

Improvements
^^^^^^^^^^^^

- Render the reviewing state of papers in the same way as abstracts
  (:issue:`3665`)

Bugfixes
^^^^^^^^

- Use correct speaker name when exporting contributions to spreadsheets
- Use friendly IDs in abstract attachment package folder names
- Fix typo in material package subcontribution folder names
- Fix check on whether registering for an event is possible
- Show static text while editing registrations (:issue:`3682`)


Version 2.1.4
-------------

*Released on September 25, 2018*

Bugfixes
^^^^^^^^

- Let managers download tickets for registrants even if all public ticket
  downloads are disabled (:issue:`3493`)
- Do not count deleted registrations when printing tickets from the badge
  designer page
- Hide "Save answers" in surveys while not logged in
- Fix importing event archives containing registrations with attachments
- Fix display issue in participants table after editing data (:issue:`3511`)
- Fix errors when booking rooms via API


Version 2.1.3
-------------

*Released on August 09, 2018*

Security fixes
^^^^^^^^^^^^^^

- Only return timetable entries for the current session when updating a
  session through the timetable (:issue:`3474`, thanks :user:`glunardi`
  for reporting)
- Prevent session managers/coordinators from modifying certain timetable
  entries or scheduling contributions not assigned to their session
- Restrict access to timetable entry details to users who are authorized
  to see them

Improvements
^^^^^^^^^^^^

- Improve survey result display (:issue:`3486`)
- Improve email validation for registrations (:issue:`3471`)

Bugfixes
^^^^^^^^

- Point to correct day in "edit session timetable" link (:issue:`3419`)
- Fix error when exporting abstracts with review questions to JSON
- Point the timetable to correct day in the session details
- Fix massive performance issue on the material package page in big events
- Fix error when using the checkin app to mark someone as checked in
  (:issue:`3473`, thanks :user:`femtobit`)
- Fix error when a session coordinator tries changing the color of a break
  using the color picker in the balloon's tooltip

Internal Changes
^^^^^^^^^^^^^^^^
- Add some new signals and template hooks to the registration module


Version 2.1.2
-------------

*Released on June 11, 2018*

Improvements
^^^^^^^^^^^^

- Show email address for non-anonymous survey submissions
  (:issue:`3258`)

Bugfixes
^^^^^^^^

- Show question description in survey results (:issue:`3383`)
- Allow paper managers to submit paper revisions
- Fix error when not providing a URL for privacy policy or terms
- Use consistent order for privacy/terms links in the footer
- Fix cloning of locked events


Version 2.1.1
-------------

*Released on May 31, 2018*

Improvements
^^^^^^^^^^^^

- Add a privacy policy page linked from the footer (:issue:`1415`)
- Terms & Conditions can now link to an external URL
- Show a warning to all admins if Celery is not running or outdated
- Add registration ID placeholder for badges (:issue:`3370`, thanks
  :user:`bpedersen2`)

Bugfixes
^^^^^^^^

- Fix alignment issue in the "Indico Weeks View" timetable theme
  (:issue:`3367`)
- Reset visibility when cloning an event to a different category
  (:issue:`3372`)


Version 2.1
-----------

*Released on May 16, 2018*

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
- Use event timezone when displaying event log entries (:issue:`3354`)
- Correctly render most markdown elements when generating a programme PDF
  (:issue:`3351`)
- Do not send any emails when trying to approve/reject a registration
  that is not pending (:issue:`3358`)

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
