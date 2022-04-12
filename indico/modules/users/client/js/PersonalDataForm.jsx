// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
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
import {Field, Form as FinalForm, FormSpy, useField, useForm} from 'react-final-form';
import {Form} from 'semantic-ui-react';

import {
  FinalDropdown,
  FinalInput,
  FinalSubmitButton,
  getChangedValues,
  handleSubmitError,
  parsers as p,
} from 'indico/react/forms';
import {Translate, Param} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import './PersonalDataForm.module.scss';

function SyncedFinalInput({name, syncedValues, readOnly, required, ...rest}) {
  const form = useForm();
  const {
    input: {onChange: setSyncedFields, value: syncedFields},
  } = useField('synced_fields');

  const syncable = syncedValues[name] !== undefined && (!required || syncedValues[name]);

  return (
    <FinalInput
      {...rest}
      name={name}
      styleName={syncable ? 'syncable' : ''}
      readOnly={readOnly || syncedFields.includes(name)}
      required={required}
      action={
        syncable
          ? {
              type: 'button',
              active: syncedFields.includes(name),
              icon: 'sync',
              toggle: true,
              className: 'ui-qtip',
              title: Translate.string('Toggle synchronization of this field'),
              onClick: () => {
                if (syncedFields.includes(name)) {
                  setSyncedFields(syncedFields.filter(x => x !== name));
                } else {
                  setSyncedFields([...syncedFields, name].sort());
                  form.change(name, syncedValues[name]);
                }
              },
            }
          : undefined
      }
    />
  );
}

SyncedFinalInput.propTypes = {
  name: PropTypes.string.isRequired,
  syncedValues: PropTypes.objectOf(PropTypes.string).isRequired,
  readOnly: PropTypes.bool,
  required: PropTypes.bool,
};

SyncedFinalInput.defaultProps = {
  readOnly: false,
  required: false,
};

function PersonalDataForm({userId, userValues, titles, syncedValues}) {
  const userIdArgs = userId !== null ? {user_id: userId} : {};

  const handleSubmit = async (data, form) => {
    const changedValues = getChangedValues(data, form);
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
              />
              <SyncedFinalInput
                name="last_name"
                label={Translate.string('Last name')}
                required
                syncedValues={syncedValues}
              />
            </Form.Group>
            <SyncedFinalInput
              name="affiliation"
              label={Translate.string('Affiliation')}
              syncedValues={syncedValues}
            />
            <SyncedFinalInput
              name="address"
              label={Translate.string('Address')}
              syncedValues={syncedValues}
            />
            <SyncedFinalInput
              name="phone"
              label={Translate.string('Phone number')}
              syncedValues={syncedValues}
            />
            <SyncedFinalInput
              name="email"
              label={Translate.string('Email address')}
              syncedValues={syncedValues}
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
            <FormSpy>{f => <pre>{JSON.stringify(f.values, null, 2)}</pre>}</FormSpy>
          </Form>
        )}
      </FinalForm>
    </div>
  );
}

PersonalDataForm.propTypes = {
  userId: PropTypes.number,
  userValues: PropTypes.object.isRequired,
  titles: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
    })
  ).isRequired,
  syncedValues: PropTypes.objectOf(PropTypes.string).isRequired,
};

PersonalDataForm.defaultProps = {
  userId: null,
};

window.setupPersonalDataForm = function setupPersonalDataForm(
  userId,
  userValues,
  titles,
  syncedValues
) {
  document.addEventListener('DOMContentLoaded', () => {
    ReactDOM.render(
      <PersonalDataForm
        userId={userId}
        userValues={userValues}
        titles={titles}
        syncedValues={syncedValues}
      />,
      document.querySelector('#personal-details-form-container')
    );
  });
};
