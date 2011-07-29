.. _event_evaluation:

================
Event Evaluation
================

Introduction
------------

With this evaluation module for Indico you can create your own
online web survey in order to know participants' opinion about the
conferences/seminars/lectures.

--------------

Functional goals
----------------

Security
~~~~~~~~

Survey questions and statistical results are neither vital nor
confidential for CERN members. We believe standard precautions are
enough within this application. A survey will inherit access and
modification rights from the event it belongs to. In other words,
only users who are allowed to see an event will be able to have
access to and fill in the evaluation form. The survey can only be
altered in the Management Area. This means that only users who are
already allowed to edit an event can create a survey, modify it and
view the statistical results.

--------------

Usability
~~~~~~~~~

The main possible actions for the **surveyor** *(management area)*
are the following:

* Create/edit an evaluation form concerning an event.
* Edit its options and status (visible/hidden).
* Possibility of setting that only logged users have access to the
  form.
* Create/edit questions contained in this form.
* Ability to preview a form while editing it.
* Import/export an evaluation in order to back it up or facilitate
  further creations.
* See the statistics of the results.
* Export statistics to a CSV file.
* Possibility of seeing/deleting individual answers in the results.
* Ability to send the evaluation link automatically by email to the
  participants at the start.
* Possibility of editing a survey in process even if some people have
  already answered it.

For a **submitter** *(display area)*:

* Access to the survey via the menu of an event.
* Logged users can always modify their already submitted forms.

--------------

Interface
---------

Management Area
~~~~~~~~~~~~~~~

In the *Evaluation* option we have four
tabs: *Setup \| Edit \| Preview \| Results*.

--------------

Setup
^^^^^

In this section you can set the main information and configuration
about the survey. Click on |image174| to set your options.

|image175|

-
   **Curent status:** When an evaluation is HIDDEN (default), it is
   not shown in the Display Area and guests cannot answer it. You can
   show the evaluation by setting it to VISIBLE. But be aware that if
   you want your survey to work properly it must be open and contain
   some questions. To show/hide it, simply click on |image176| /
   |image177|.

-
   **Notifications:** You can set email addresses of people you want
   to be notified when the evaluation starts and/or when someone
   answers the form. ``Advice``: Click on *modify* and then check
   *Add current registrants* if you want your event participants to be
   notified of the start of the evaluation.

-
   **Must have an account:** If an account is needed, visitors must
   first log in before accessing the form.

-
   **Anonymous:** When anonymous, logged submitters send their form
   anonymously. Otherwise their identity is known by the surveyor.
   ``Note``: Users not logged in can always send their form anonymously.
   If you really need to know the identity of all your submitters, you
   have to click on *modify* then check *Must have an account*.

-
   **Special Actions:**

   -
      |image178| Export the evaluation with its questions to an XML
      file. Useful for backing up or transporting. *Note:* If the file is
      directly shown in Firefox/InternetExplorer6, save it with:
      *File > Save as...* To solve the same problem in InternetExplorer7:
      *Page > Save as...*

   -
      |image179| Import an evaluation from an XML file.

      |image180|

      Concerning the main setup configuration (all the main information, e.g.,
      title, announcement, etc.) you can choose to keep your current one
      or to overwrite it with an imported one. For the questions, you can
      keep only your current ones or only imported ones or have both
      (imported ones just after current ones). ``Advice``: We suggest that you
      back up your current evaluation (with export feature) before
      importing in order to prevent loss of data. ``Note``: In order to
      prevent some misunderstanding the status and the dates are not
      imported. Be aware that as questions and submissions are bound, you
      will also lose your current submissions if you get rid of your
      questions.

   -  |image181| All collected answers will be erased.

   -
      |image182| All questions will be erased. As the submissions are
      connected to them, they will also be removed!

   -
      |image183| Delete all evaluation informations, its questions and
      its submissions. You will have a brand new evaluation.

--------------

Edit
^^^^

In this section you can add/edit/remove the questions in your
form. On the left panel you have six different types of question you
can add.

-
   |image184| **Textbox:** A standard field where your submitter can
   enter some text as answer to the provided question. Here is a
   little example of a question of type Textbox.

   |image185|

-
   |image186| **Textarea:** Like Textbox but with more capacity for
   text. Suitable for long answers like comments, feedbacks, etc.

   |image187|

-
   |image188| **Password:** Like Textbox but the answer is hidden.
   For example on the picture below, it is recommended that the answer
   is hidden if the submitter is in a public area. Otherwise anybody
   next to him would be able to read the password on the screen. Note
   that the evaluation module doesn't use https, as all this
   information is not supposed to be confidential.

   |image189|

-
   |image190| **Select:** A drop down list which lets the submitter
   select one answer.

   |image191|

-
   |image192| **Radio:** A group of radio buttons which lets the
   submitter select one answer.

   |image193|

-
   |image194| **Checkbox:** This type is suitable for multiple-choice
   questions. You can check more than one answer.

   |image195|


When adding a Textbox/Textarea/Password you have the screen below.

|image196|


-
   **Required:** If checked, an answer for this question is
   mandatory.

-  **Question:** Enter your question.

-
   **Keyword:** A keyword is the summary of the question in one
   word. (e.g. "What is your name?" -> "name") It's useful when
   exporting the statistics into a CSV file. Instead of writing the
   full question, we just write the keyword so that it takes less
   place.

-  **Description:** Enter a description (optional).

-  **Help:** Enter a help message (optional).

-
   **Default answer:** The answer to the question will already be
   filled in with this given default answer (optional).

-
   **Position in form:** The position of the question within the
   form.


On the following picture you can see the result of the
manipulation.

|image197|

When adding a Select/Radio/Checkbox you have the screen below. Note
that some fields have already been described above, which is why they
are not explained here.

|image198|

* **Choice Items:** Choice items are answers that can be selected.
  ``Note``: Check the box next to a choice item, to set it to be a
  default answer.

On the following picture you can see the result of the
manipulation.

|image199|

After having first added some questions, here is an example of the
questions overview (see picture below). You can change the position
of a question within the form by clicking on |image201|. Press
|image202| to edit a question and |image203| to remove it.

|image200|


--------------

Preview
^^^^^^^

In Preview you can see what your evaluation really looks like in
the display area. Feel free to play with this form, submitted
information won't be recorded.

--------------

Results
^^^^^^^

In this section we have the statistics. There are two panels
called *Options* and *Statistics*.

In the first one you can select which submissions you want to
see, remove some of them, and export all the results into a CSV
file.

To import a CSV file into Microsoft Office Excel: *Data* >
*Import External Data* > *Import Data...* > select your CSV file >
*Next* > Uncheck *Tab* and check *Comma* > *Next* > *Finish* >
*OK*.

In the second, you see the collected results of your evaluation
shown as graphs or as answer lists depending on the question
type.

Answer lists shown for Textbox/Textarea/Password:

|image204|

Graphs shown for Select/Radio/Checkbox:

|image205|

--------------

Display Area
~~~~~~~~~~~~

For a conference, you can access an evaluation via the left menu.

For a meeting/lecture, you can access it via the top menu.

|image207|

--------------

.. |image172| image:: UserGuidePics/enabledSection.png
.. |image173| image:: UserGuidePics/eval_ManagementFeature.png
.. |image174| image:: UserGuidePics/eval_modify.png
.. |image175| image:: UserGuidePics/eval_Setup.jpg
.. |image176| image:: UserGuidePics/eval_show.png
.. |image177| image:: UserGuidePics/eval_hide.png
.. |image178| image:: UserGuidePics/eval_exportEval.png
.. |image179| image:: UserGuidePics/eval_importEval.png
.. |image180| image:: UserGuidePics/eval_ImportXml.png
.. |image181| image:: UserGuidePics/eval_removeSubmissions.png
.. |image182| image:: UserGuidePics/eval_removeQuestions.png
.. |image183| image:: UserGuidePics/eval_reinit.png
.. |image184| image:: UserGuidePics/eval_textbox.png
.. |image185| image:: UserGuidePics/eval_textboxEx.png
.. |image186| image:: UserGuidePics/eval_textarea.png
.. |image187| image:: UserGuidePics/eval_textareaEx.png
.. |image188| image:: UserGuidePics/eval_password.png
.. |image189| image:: UserGuidePics/eval_passwordEx.png
.. |image190| image:: UserGuidePics/eval_select.png
.. |image191| image:: UserGuidePics/eval_selectEx.png
.. |image192| image:: UserGuidePics/eval_radio.png
.. |image193| image:: UserGuidePics/eval_radioEx.png
.. |image194| image:: UserGuidePics/eval_checkbox.png
.. |image195| image:: UserGuidePics/eval_checkboxEx.png
.. |image196| image:: UserGuidePics/eval_addBox.png
.. |image197| image:: UserGuidePics/eval_addedBox.jpg
.. |image198| image:: UserGuidePics/eval_addChoice.png
.. |image199| image:: UserGuidePics/eval_addedChoice.jpg
.. |image200| image:: UserGuidePics/eval_questionsView.jpg
.. |image201| image:: UserGuidePics/eval_position.jpg
.. |image202| image:: UserGuidePics/edit.png
.. |image203| image:: UserGuidePics/remove.png
.. |image204| image:: UserGuidePics/eval_result1.png
.. |image205| image:: UserGuidePics/eval_result6.png
.. |image206| image:: UserGuidePics/eval_DisplayConf.jpg
.. |image207| image:: UserGuidePics/eval_DisplayMeetingLecture.png
