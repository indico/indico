// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchAffiliationURL from 'indico-url:users.api_affiliations';
import emailsURL from 'indico-url:users.user_emails';
import saveURL from 'indico-url:users.user_profile_update';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import {Field, Form as FinalForm, useField, useForm} from 'react-final-form';
import {Form, Header} from 'semantic-ui-react';

import {
  FinalComboDropdown,
  FinalDropdown,
  FinalInput,
  FinalSubmitButton,
  FinalTextArea,
  getChangedValues,
  handleSubmitError,
  parsers as p,
} from 'indico/react/forms';
import {Translate, Param} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import './PersonalDataForm.module.scss';

const debounce = makeAsyncDebounce(250);

function SyncedFinalField({
  name,
  syncName,
  as: FieldComponent,
  syncedValues,
  readOnly,
  required,
  processSyncedValue,
  ...rest
}) {
  const form = useForm();
  const {
    input: {onChange: setSyncedFields, value: syncedFields},
  } = useField('synced_fields');

  if (!syncName) {
    syncName = name;
  }

  const syncable = syncedValues[syncName] !== undefined && (!required || syncedValues[syncName]);

  return (
    <FieldComponent
      {...rest}
      name={name}
      styleName={syncable ? 'syncable' : ''}
      readOnly={readOnly || (syncable && syncedFields.includes(syncName))}
      required={required}
      action={
        syncable
          ? {
              type: 'button',
              active: syncedFields.includes(syncName),
              icon: 'sync',
              toggle: true,
              className: 'ui-qtip',
              title: Translate.string('Toggle synchronization of this field'),
              onClick: () => {
                if (syncedFields.includes(syncName)) {
                  setSyncedFields(syncedFields.filter(x => x !== syncName));
                  form.change(name, form.getFieldState(name).initial);
                } else {
                  setSyncedFields([...syncedFields, syncName].sort());
                  form.change(name, processSyncedValue(syncedValues[syncName]));
                }
              },
            }
          : undefined
      }
    />
  );
}

SyncedFinalField.propTypes = {
  name: PropTypes.string.isRequired,
  syncName: PropTypes.string,
  as: PropTypes.elementType.isRequired,
  syncedValues: PropTypes.objectOf(PropTypes.string).isRequired,
  readOnly: PropTypes.bool,
  required: PropTypes.bool,
  processSyncedValue: PropTypes.func,
};

SyncedFinalField.defaultProps = {
  syncName: null,
  readOnly: false,
  required: false,
  processSyncedValue: x => x,
};

function SyncedFinalInput(props) {
  return <SyncedFinalField as={FinalInput} {...props} />;
}

function SyncedFinalTextArea(props) {
  return <SyncedFinalField as={FinalTextArea} {...props} />;
}

function SyncedFinalComboDropdown(props) {
  return <SyncedFinalField as={FinalComboDropdown} {...props} />;
}

function PersonalDataForm({
  userId,
  userValues,
  currentAffiliation,
  titles,
  syncedValues,
  hasPredefinedAffiliations,
}) {
  const userIdArgs = userId !== null ? {user_id: userId} : {};
  const [_affiliationResults, setAffiliationResults] = useState([]);
  const affiliationResults =
    currentAffiliation && !_affiliationResults.find(x => x.id === currentAffiliation.id)
      ? [currentAffiliation, ..._affiliationResults]
      : _affiliationResults;

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
  const affiliationOptions = affiliationResults.map(res => ({
    key: res.id,
    value: res.id,
    text: `${res.name} `, // XXX: the space allows addition even if the entered text matches a result item
    content: (
      <Header
        content={res.name}
        subheader={[res.street, res.postcode, res.city, res.country_code]
          .filter(x => x)
          .map((x, i) => (
            // eslint-disable-next-line react/no-array-index-key
            <React.Fragment key={i}>
              {i !== 0 && <br />}
              {x}
            </React.Fragment>
          ))}
      />
    ),
  }));

  const searchAffiliationChange = async (evt, {searchQuery}) => {
    if (!searchQuery) {
      setAffiliationResults([]);
      return;
    }
    let resp;
    try {
      resp = await debounce(() => indicoAxios.get(searchAffiliationURL({q: searchQuery})));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setAffiliationResults(resp.data);
  };

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
            {hasPredefinedAffiliations ? (
              <SyncedFinalComboDropdown
                name="affiliation_data"
                syncName="affiliation"
                processSyncedValue={x => ({id: null, text: x})}
                options={affiliationOptions}
                fluid
                additionLabel={Translate.string('Use custom affiliation:') + ' '} // eslint-disable-line prefer-template
                onSearchChange={searchAffiliationChange}
                placeholder={Translate.string('Select an affiliation or add your own')}
                noResultsMessage={Translate.string('Search an affiliation or enter one manually')}
                renderCustomOptionContent={value => (
                  <Header
                    content={value}
                    subheader={Translate.string('You entered this option manually')}
                  />
                )}
                label={Translate.string('Affiliation')}
                syncedValues={syncedValues}
              />
            ) : (
              <SyncedFinalInput
                name="affiliation"
                label={Translate.string('Affiliation')}
                syncedValues={syncedValues}
              />
            )}
            <SyncedFinalTextArea
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
        hasPredefinedAffiliations={hasPredefinedAffiliations}
      />,
      document.querySelector('#personal-details-form-container')
    );
  });
};
