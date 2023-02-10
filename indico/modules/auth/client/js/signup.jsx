// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import {Field, Form as FinalForm} from 'react-final-form';
import {Button, Form, Message} from 'semantic-ui-react';

import {
  SyncedFinalAffiliationDropdown,
  SyncedFinalDropdown,
  SyncedFinalInput,
  SyncedFinalTextArea,
} from 'indico/react/components/syncedInputs';
import {
  FinalInput,
  FinalSubmitButton,
  handleSubmitError,
  getValuesForFields,
} from 'indico/react/forms';
import {Fieldset, FinalTextArea} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

function Signup({
  cancelURL,
  moderated,
  initialValues,
  hasPredefinedAffiliations,
  showAccountForm,
  syncedValues,
  emails,
  affiliationMeta,
  hasPendingUser,
  mandatoryFields,
  lockedFields,
  lockedFieldMessage,
}) {
  const handleSubmit = async (data, form) => {
    const values = getValuesForFields(data, form);
    delete values.password_confirm;
    if (!hasPredefinedAffiliations) {
      // value.affiliation is already there and used
      delete values.affiliation_data;
    } else if (values.affiliation_data) {
      values.affiliation = values.affiliation_data.text.trim();
      values.affiliation_id = values.affiliation_data.id;
      delete values.affiliation_data;
    }
    let resp;
    try {
      resp = await indicoAxios.post(location.href, values);
    } catch (e) {
      return handleSubmitError(
        e,
        hasPredefinedAffiliations ? {affiliation: 'affiliation_data'} : {}
      );
    }
    location.href = resp.data.redirect;
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  return (
    <FinalForm
      onSubmit={handleSubmit}
      initialValues={initialValues}
      initialValuesEqual={_.isEqual}
      subscription={{submitting: true}}
      validate={values => {
        const errors = {};
        if (
          values.password &&
          values.password_confirm &&
          values.password_confirm !== values.password
        ) {
          errors.password_confirm = Translate.string('Passwords must match');
        }
        return errors;
      }}
    >
      {fprops => (
        <Form onSubmit={fprops.handleSubmit}>
          {!showAccountForm && (
            <Field name="synced_fields" isEqual={_.isEqual} render={() => null} />
          )}
          {hasPendingUser && (
            <Message info>
              <Translate>
                There is already some information in Indico that concerns you. We are going to link
                it automatically.
              </Translate>
            </Message>
          )}
          <Fieldset
            legend={Translate.string('User information')}
            active={showAccountForm || moderated}
          >
            {emails.length > 1 ? (
              <SyncedFinalDropdown
                name="email"
                label={Translate.string('Email address')}
                options={emails.map(e => ({
                  key: e,
                  value: e,
                  text: e,
                }))}
                syncedValues={syncedValues}
                lockedFields={lockedFields}
                lockedFieldMessage={lockedFieldMessage}
                required
              />
            ) : (
              <SyncedFinalInput
                name="email"
                label={Translate.string('Email address')}
                syncedValues={syncedValues}
                lockedFields={lockedFields}
                lockedFieldMessage={lockedFieldMessage}
                readOnly
              />
            )}
            <Form.Group widths="equal">
              <SyncedFinalInput
                name="first_name"
                label={Translate.string('First name')}
                required
                syncedValues={syncedValues}
                lockedFields={lockedFields}
                lockedFieldMessage={lockedFieldMessage}
              />
              <SyncedFinalInput
                name="last_name"
                label={Translate.string('Last name')}
                required
                syncedValues={syncedValues}
                lockedFields={lockedFields}
                lockedFieldMessage={lockedFieldMessage}
              />
            </Form.Group>
            {hasPredefinedAffiliations ? (
              <SyncedFinalAffiliationDropdown
                name="affiliation_data"
                required={moderated && mandatoryFields.includes('affiliation')}
                syncName="affiliation"
                syncedValues={syncedValues}
                lockedFields={lockedFields}
                lockedFieldMessage={lockedFieldMessage}
                currentAffiliation={affiliationMeta}
              />
            ) : (
              <SyncedFinalInput
                name="affiliation"
                label={Translate.string('Affiliation')}
                required={moderated && mandatoryFields.includes('affiliation')}
                syncedValues={syncedValues}
                lockedFields={lockedFields}
                lockedFieldMessage={lockedFieldMessage}
              />
            )}
            {'address' in syncedValues && (
              <SyncedFinalTextArea
                name="address"
                label={Translate.string('Address')}
                syncedValues={syncedValues}
                lockedFields={lockedFields}
                lockedFieldMessage={lockedFieldMessage}
              />
            )}
            {'phone' in syncedValues && (
              <SyncedFinalInput
                name="phone"
                label={Translate.string('Phone number')}
                syncedValues={syncedValues}
                lockedFields={lockedFields}
                lockedFieldMessage={lockedFieldMessage}
              />
            )}
          </Fieldset>
          {showAccountForm && (
            <Fieldset legend={Translate.string('Login details')}>
              <FinalInput name="username" label={Translate.string('Username')} required />
              <Form.Group widths="equal">
                <FinalInput
                  name="password"
                  type="password"
                  label={Translate.string('Password')}
                  autoComplete="new-password"
                  required
                />
                <FinalInput
                  name="password_confirm"
                  type="password"
                  label={Translate.string('Confirm password')}
                  autoComplete="new-password"
                  required
                />
              </Form.Group>
            </Fieldset>
          )}
          {moderated && (
            <Fieldset legend={Translate.string('Account moderation')}>
              <Message info>
                <Translate>
                  Each new account needs to be approved by an administrator. We will send you an
                  email as soon as your request has been approved.
                </Translate>
              </Message>
              <FinalTextArea
                required={mandatoryFields.includes('comment')}
                name="comment"
                initialValue=""
                label={Translate.string('Comment')}
                description={Translate.string(
                  'You can provide additional information or a comment for the administrators who will review your registration.'
                )}
              />
            </Fieldset>
          )}
          <div style={{display: 'flex', justifyContent: 'flex-end'}}>
            <FinalSubmitButton
              disabledUntilChange={false}
              label={
                moderated
                  ? Translate.string('Submit registration request')
                  : Translate.string('Create my Indico profile')
              }
              className="submit-button"
            />
            <Form.Field disabled={fprops.submitting}>
              <Button as="a" href={cancelURL} disabled={fprops.submitting}>
                <Translate>Cancel</Translate>
              </Button>
            </Form.Field>
          </div>
        </Form>
      )}
    </FinalForm>
  );
}

Signup.propTypes = {
  cancelURL: PropTypes.string.isRequired,
  moderated: PropTypes.bool.isRequired,
  initialValues: PropTypes.object.isRequired,
  hasPredefinedAffiliations: PropTypes.bool.isRequired,
  showAccountForm: PropTypes.bool.isRequired,
  syncedValues: PropTypes.object.isRequired,
  emails: PropTypes.arrayOf(PropTypes.string).isRequired,
  affiliationMeta: PropTypes.object,
  hasPendingUser: PropTypes.bool,
  mandatoryFields: PropTypes.arrayOf(PropTypes.string).isRequired,
  lockedFields: PropTypes.arrayOf(PropTypes.string),
  lockedFieldMessage: PropTypes.string,
};

Signup.defaultProps = {
  affiliationMeta: null,
  hasPendingUser: false,
  lockedFields: [],
  lockedFieldMessage: '',
};

document.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('#signup-container');
  if (!container) {
    return;
  }

  const config = JSON.parse(container.dataset.config);
  ReactDOM.render(<Signup {...config} />, container);
});
