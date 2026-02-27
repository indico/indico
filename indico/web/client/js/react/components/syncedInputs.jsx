// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useField, useForm} from 'react-final-form';
import {Form, Popup} from 'semantic-ui-react';

import {FinalDropdown, FinalInput, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import FinalAffiliationField from './FinalAffiliationField';

import './syncedInputs.module.scss';

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

export function SyncedFinalAffiliationDropdown({
  name,
  required,
  syncName,
  syncedValues,
  lockedFields,
  lockedFieldMessage,
  currentAffiliation,
  allowCustomAffiliations,
}) {
  return (
    <SyncedFinalField
      as={FinalAffiliationField}
      name={name}
      required={required}
      validate={v =>
        required && !v?.text ? Translate.string('This field is required.') : undefined
      }
      syncName={syncName}
      processSyncedValue={(value, values) => ({id: values.affiliation_id || null, text: value})}
      currentAffiliation={currentAffiliation}
      allowCustomAffiliations={allowCustomAffiliations}
      label={Translate.string('Affiliation')}
      syncedValues={syncedValues}
      lockedFields={lockedFields}
      lockedFieldMessage={lockedFieldMessage}
      hasPredefinedAffiliations
      fluid
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
  allowCustomAffiliations: PropTypes.bool,
};

SyncedFinalAffiliationDropdown.defaultProps = {
  required: false,
  syncName: null,
  currentAffiliation: null,
  allowCustomAffiliations: true,
};
