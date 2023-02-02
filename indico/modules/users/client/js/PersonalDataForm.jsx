// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import emailsURL from 'indico-url:users.user_emails';
import saveURL from 'indico-url:users.user_profile_update';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import {Field, Form as FinalForm} from 'react-final-form';
import {Form} from 'semantic-ui-react';

import {
  SyncedFinalAffiliationDropdown,
  SyncedFinalInput,
  SyncedFinalTextArea,
} from 'indico/react/components/syncedInputs';
import {
  FinalDropdown,
  FinalSubmitButton,
  getChangedValues,
  handleSubmitError,
  parsers as p,
} from 'indico/react/forms';
import {Translate, Param} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

function PersonalDataForm({
  userId,
  userValues,
  currentAffiliation,
  titles,
  syncedValues,
  lockedFields,
  hasPredefinedAffiliations,
}) {
  const userIdArgs = userId !== null ? {user_id: userId} : {};

  const handleSubmit = async (data, form) => {
    const changedValues = getChangedValues(data, form);
    if (!hasPredefinedAffiliations) {
      // value.affiliation is already there and used
      delete changedValues.affiliation_data;
    } else if (changedValues.affiliation_data) {
      changedValues.affiliation = changedValues.affiliation_data.text.trim();
      changedValues.affiliation_id = changedValues.affiliation_data.id;
      delete changedValues.affiliation_data;
    }
    try {
      await indicoAxios.patch(saveURL(userIdArgs), changedValues);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const titleOptions = titles.map(t => ({key: t.name, value: t.name, text: t.title}));

  return (
    <div>
      <FinalForm
        onSubmit={handleSubmit}
        initialValues={userValues}
        initialValuesEqual={_.isEqual}
        subscription={{}}
      >
        {fprops => (
          <Form onSubmit={fprops.handleSubmit}>
            <Field name="synced_fields" isEqual={_.isEqual} render={() => null} />
            <FinalDropdown
              name="title"
              options={titleOptions}
              selection
              parse={p.nullIfEmpty}
              label={Translate.string('Title')}
              placeholder={Translate.string('None')}
            />
            <Form.Group widths="equal">
              <SyncedFinalInput
                name="first_name"
                label={Translate.string('First name')}
                required
                syncedValues={syncedValues}
                lockedFields={lockedFields}
              />
              <SyncedFinalInput
                name="last_name"
                label={Translate.string('Last name')}
                required
                syncedValues={syncedValues}
                lockedFields={lockedFields}
              />
            </Form.Group>
            {hasPredefinedAffiliations ? (
              <SyncedFinalAffiliationDropdown
                name="affiliation_data"
                syncName="affiliation"
                currentAffiliation={currentAffiliation}
                syncedValues={syncedValues}
                lockedFields={lockedFields}
              />
            ) : (
              <SyncedFinalInput
                name="affiliation"
                label={Translate.string('Affiliation')}
                syncedValues={syncedValues}
                lockedFields={lockedFields}
              />
            )}
            <SyncedFinalTextArea
              name="address"
              label={Translate.string('Address')}
              syncedValues={syncedValues}
              lockedFields={lockedFields}
            />
            <SyncedFinalInput
              name="phone"
              label={Translate.string('Phone number')}
              syncedValues={syncedValues}
              lockedFields={lockedFields}
            />
            <SyncedFinalInput
              name="email"
              label={Translate.string('Email address')}
              syncedValues={syncedValues}
              lockedFields={lockedFields}
              readOnly
            >
              <Translate>
                You can manage your email addresses{' '}
                <Param name="link" wrapper={<a href={emailsURL(userIdArgs)} />}>
                  here
                </Param>
                .
              </Translate>
            </SyncedFinalInput>
            <FinalSubmitButton label={Translate.string('Save changes')} className="submit-button" />
          </Form>
        )}
      </FinalForm>
    </div>
  );
}

PersonalDataForm.propTypes = {
  userId: PropTypes.number,
  userValues: PropTypes.object.isRequired,
  currentAffiliation: PropTypes.object,
  titles: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
    })
  ).isRequired,
  syncedValues: PropTypes.objectOf(PropTypes.string).isRequired,
  lockedFields: PropTypes.arrayOf(PropTypes.string).isRequired,
  hasPredefinedAffiliations: PropTypes.bool.isRequired,
};

PersonalDataForm.defaultProps = {
  userId: null,
  currentAffiliation: null,
};

window.setupPersonalDataForm = function setupPersonalDataForm(
  userId,
  userValues,
  currentAffiliation,
  titles,
  syncedValues,
  lockedFields,
  hasPredefinedAffiliations
) {
  document.addEventListener('DOMContentLoaded', () => {
    ReactDOM.render(
      <PersonalDataForm
        userId={userId}
        userValues={userValues}
        currentAffiliation={currentAffiliation}
        titles={titles}
        syncedValues={syncedValues}
        lockedFields={lockedFields}
        hasPredefinedAffiliations={hasPredefinedAffiliations}
      />,
      document.querySelector('#personal-details-form-container')
    );
  });
};
