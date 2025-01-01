// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchAffiliationURL from 'indico-url:users.api_affiliations';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useField, useForm} from 'react-final-form';
import {Form, Header, Popup} from 'semantic-ui-react';

import {FinalComboDropdown, FinalDropdown, FinalInput, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import './syncedInputs.module.scss';

const debounce = makeAsyncDebounce(250);

function SyncedFinalField({
  name,
  syncName,
  as: FieldComponent,
  syncedValues,
  lockedFields,
  lockedFieldMessage,
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
  const synced = syncedFields.includes(syncName);
  const locked = lockedFields.includes(syncName);

  const field = (
    <FieldComponent
      {...rest}
      name={name}
      styleName={syncable ? 'syncable' : ''}
      readOnly={readOnly || (syncable && synced)}
      required={required}
      action={
        syncable
          ? {
              type: 'button',
              active: synced,
              disabled: synced && locked,
              icon: 'sync',
              toggle: true,
              className: 'ui-qtip',
              title: Translate.string('Toggle synchronization of this field'),
              onClick: () => {
                if (synced) {
                  setSyncedFields(syncedFields.filter(x => x !== syncName));
                  form.change(name, form.getFieldState(name).initial);
                } else {
                  setSyncedFields([...syncedFields, syncName].sort());
                  form.change(name, processSyncedValue(syncedValues[syncName], syncedValues));
                }
              },
            }
          : undefined
      }
    />
  );
  if (synced && syncable && locked && lockedFieldMessage) {
    return (
      <Popup
        on="hover"
        position="bottom left"
        content={lockedFieldMessage}
        trigger={<Form.Field>{field}</Form.Field>}
      />
    );
  } else {
    return field;
  }
}

SyncedFinalField.propTypes = {
  name: PropTypes.string.isRequired,
  syncName: PropTypes.string,
  as: PropTypes.elementType.isRequired,
  syncedValues: PropTypes.object.isRequired,
  lockedFields: PropTypes.arrayOf(PropTypes.string).isRequired,
  lockedFieldMessage: PropTypes.string.isRequired,
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

export function SyncedFinalInput(props) {
  return <SyncedFinalField as={FinalInput} {...props} />;
}

export function SyncedFinalTextArea(props) {
  return <SyncedFinalField as={FinalTextArea} {...props} />;
}

export function SyncedFinalDropdown(props) {
  return <SyncedFinalField as={FinalDropdown} selection fluid {...props} />;
}

// TODO: see if we can't converge with FinalAffiliationField to remove the duplicated code...
export function SyncedFinalAffiliationDropdown({
  name,
  required,
  syncName,
  syncedValues,
  lockedFields,
  lockedFieldMessage,
  currentAffiliation,
}) {
  const [_affiliationResults, setAffiliationResults] = useState([]);
  const affiliationResults =
    currentAffiliation && !_affiliationResults.find(x => x.id === currentAffiliation.id)
      ? [currentAffiliation, ..._affiliationResults]
      : _affiliationResults;

  const getSubheader = ({city, country_name: countryName}) => {
    if (city && countryName) {
      return `${city}, ${countryName}`;
    }
    return city || countryName;
  };

  const affiliationOptions = affiliationResults.map(res => ({
    key: res.id,
    value: res.id,
    text: `${res.name} `, // XXX: the space allows addition even if the entered text matches a result item
    content: <Header style={{fontSize: 14}} content={res.name} subheader={getSubheader(res)} />,
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
    <SyncedFinalField
      as={FinalComboDropdown}
      name={name}
      required={required}
      validate={v =>
        required && !v?.text ? Translate.string('This field is required.') : undefined
      }
      syncName={syncName}
      processSyncedValue={(value, values) => ({id: values.affiliation_id || null, text: value})}
      options={affiliationOptions}
      fluid
      additionLabel={Translate.string('Use custom affiliation:') + ' '} // eslint-disable-line prefer-template
      onSearchChange={searchAffiliationChange}
      placeholder={Translate.string('Select an affiliation or add your own')}
      noResultsMessage={Translate.string('Search an affiliation or enter one manually')}
      renderCustomOptionContent={value => (
        <Header content={value} subheader={Translate.string('You entered this option manually')} />
      )}
      label={Translate.string('Affiliation')}
      syncedValues={syncedValues}
      lockedFields={lockedFields}
      lockedFieldMessage={lockedFieldMessage}
    />
  );
}

SyncedFinalAffiliationDropdown.propTypes = {
  name: PropTypes.string.isRequired,
  required: PropTypes.bool,
  syncName: PropTypes.string,
  syncedValues: PropTypes.object.isRequired,
  lockedFields: PropTypes.arrayOf(PropTypes.string).isRequired,
  lockedFieldMessage: PropTypes.string.isRequired,
  currentAffiliation: PropTypes.object,
};

SyncedFinalAffiliationDropdown.defaultProps = {
  required: false,
  syncName: null,
  currentAffiliation: null,
};
