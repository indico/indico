// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Creates a data creation / edit pop-up dialog.
 * @param {String} title The title of the popup.
 * @param {Object} userData A WatchObject that has to have the following keys/attributes:
 *                          id, title, familyName, firstName, affiliation, email, address, telephone, submission.
 *                          Its information will be displayed as initial values in the dialog.
 * @param {Function} action A callback function that will be called if the user presses ok. The function will be passed
 *                          a WatchObject with the new values.
 */
type(
  'UserDataPopup',
  ['ExclusivePopupWithButtons'],
  {
    draw: function() {
      var userData = this.userData;
      var self = this;
      self.parameterManager = new IndicoUtil.parameterManager();

      var grantSubmission = [];
      var grantManagement = [];
      var grantCoordination = [];
      var warning = [];
      if (this.grantSubmission) {
        grantSubmission = [
          $T('Grant submission rights'),
          $B(Html.checkbox({id: 'submissionCheckbox'}), userData.accessor('submission')),
        ];
        warning = [
          Html.span(
            {},
            Html.span({style: {fontWeight: 'bold'}}, $T('Note:')),
            $T(' If this person does not already have an Indico account, '),
            Html.br(),
            $T('he or she will be sent an email asking to register as a user.'),
            Html.br(),
            $T(' After the registration the user will automatically be given'),
            Html.br(),
            $T(' submission rights.')
          ),
        ];
      }
      if (this.grantManagement) {
        grantManagement = [
          $T('Give management rights'),
          $B(Html.checkbox({}), userData.accessor('manager')),
        ];
        warning = [
          Html.span(
            {},
            Html.span({style: {fontWeight: 'bold'}}, $T('Note:')),
            $T(' If this person does not already have an Indico account, '),
            Html.br(),
            $T('he or she will be sent an email asking to create an account.'),
            Html.br(),
            $T(' After the account creation the user will automatically be'),
            Html.br(),
            $T(' given management rights.')
          ),
        ];
      }

      if (this.grantCoordination) {
        grantCoordination = [
          $T('Give coordination rights'),
          $B(Html.checkbox({}), userData.accessor('coordinator')),
        ];
        warning = [
          Html.span(
            {},
            Html.span({style: {fontWeight: 'bold'}}, $T('Note:')),
            $T(' If this person does not already have an Indico account, '),
            Html.br(),
            $T('he or she will be sent an email asking to create an account.'),
            Html.br(),
            $T(' After the account creation the user will automatically be'),
            Html.br(),
            $T(' given coordination rights.')
          ),
        ];
      }
      if (this.grantManagement && this.grantCoordination) {
        warning = [
          Html.span(
            {},
            Html.span({style: {fontWeight: 'bold'}}, $T('Note:')),
            $T(' If this person does not already have an Indico account, '),
            Html.br(),
            $T('he or she will be sent an email asking to create an account.'),
            Html.br(),
            $T(' After the account creation the user will automatically be'),
            Html.br(),
            $T(' given the rights.')
          ),
        ];
      }

      var form = IndicoUtil.createFormFromMap([
        [
          $T('Title'),
          $B(
            Html.select(
              {},
              Html.option({}, ''),
              Html.option({value: 'Mr'}, $T('Mr')),
              Html.option({value: 'Mrs'}, $T('Mrs')),
              Html.option({value: 'Ms'}, $T('Ms')),
              Html.option({value: 'Dr'}, $T('Dr')),
              Html.option({value: 'Prof.'}, $T('Prof.'))
            ),
            userData.accessor('title')
          ),
        ],
        [
          $T('Family Name'),
          $B(
            self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false),
            userData.accessor('familyName')
          ),
        ],
        [
          $T('First Name'),
          $B(Html.edit({style: {width: '300px'}}), userData.accessor('firstName')),
        ],
        [
          $T('Affiliation'),
          $B(Html.edit({style: {width: '300px'}}), userData.accessor('affiliation')),
        ],
        [
          $T('Email'),
          $B(
            self.parameterManager.add(
              Html.edit({id: 'email', style: {width: '300px'}}),
              'email',
              this.allowEmptyEmail
            ),
            userData.accessor('email')
          ),
        ],
        [$T('Address'), $B(Html.textarea({style: {width: '300px'}}), userData.accessor('address'))],
        [$T('Telephone'), $B(Html.edit({style: {width: '300px'}}), userData.accessor('phone'))],
        grantSubmission,
        grantManagement,
        grantCoordination,
        warning,
      ]);

      return this.ExclusivePopupWithButtons.prototype.draw.call(this, form);
    },

    _getButtons: function() {
      var self = this;
      return [
        [
          $T('Save'),
          function() {
            if ($('#submissionCheckbox').is(':checked') && $('#email').val() == 0) {
              var popup = new WarningPopup(
                $T('Warning'),
                $T(
                  'It is not possible to grant submission rights to a participant without an email address. Please set an email address.'
                )
              );
              popup.open();
              return;
            }
            self.userData.set(
              'name',
              '{0} {1}'.format(self.userData.get('firstName'), self.userData.get('familyName'))
            );
            if (self.parameterManager.check() && self.checkPerson(self.userData)) {
              self.action(self.userData);
              if (self.autoClose) {
                self.close();
              }
            }
          },
        ],
        [
          $T('Cancel'),
          function() {
            self.close();
          },
        ],
      ];
    },
  },
  function(
    title,
    userData,
    action,
    grantSubmission,
    grantManagement,
    grantCoordination,
    allowEmptyEmail,
    autoClose,
    checkPerson
  ) {
    this.userData = userData;
    this.action = action;
    this.grantSubmission = exists(grantSubmission) ? grantSubmission : false;
    this.grantManagement = exists(grantManagement) ? grantManagement : false;
    this.grantCoordination = exists(grantCoordination) ? grantCoordination : false;
    this.allowEmptyEmail = exists(allowEmptyEmail) ? allowEmptyEmail : true;
    this.ExclusivePopup(title, function() {
      return true;
    });
    this.autoClose = exists(autoClose) ? autoClose : true;
    this.checkPerson =
      checkPerson ||
      function() {
        return true;
      };
  }
);
