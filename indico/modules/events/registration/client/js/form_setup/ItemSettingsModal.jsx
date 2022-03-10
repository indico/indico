// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormSpy} from 'react-final-form';
import {useSelector, useDispatch} from 'react-redux';
import {Message} from 'semantic-ui-react';

import {
  FinalCheckbox,
  FinalInput,
  FinalTextArea,
  getValuesForFields,
  validators as v,
  parsers as p,
} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate, Param} from 'indico/react/i18n';

import {getFieldRegistry} from '../form/fields/registry';
import {getStaticData, getItemById} from '../form/selectors';

import * as actions from './actions';
import ItemTypeDropdown from './ItemTypeDropdown';

export default function ItemSettingsModal({id, sectionId, defaultNewItemType, onClose}) {
  const dispatch = useDispatch();
  const [newItemType, setNewItemType] = useState(defaultNewItemType);
  const editing = id !== null;
  const staticData = useSelector(getStaticData);
  const {inputType: existingInputType, fieldIsRequired, ...itemData} = useSelector(state =>
    editing ? getItemById(state, id) : {}
  );
  const inputType = editing ? existingInputType : newItemType;
  const fieldRegistry = getFieldRegistry();
  const isUnsupportedField = !(inputType in fieldRegistry); // TODO remove once no longer needed
  const meta = fieldRegistry[inputType] || {};
  const SettingsComponent = meta.settingsComponent;

  const handleSubmit = async (formData, form) => {
    const data = getValuesForFields(formData, form);
    const action = editing
      ? actions.updateItem(id, data)
      : actions.createItem(sectionId, inputType, data);
    const rv = await dispatch(action);
    if (rv.error) {
      return rv.error;
    }
    onClose();
  };

  let initialValues = itemData;
  if (!editing) {
    initialValues = _.isFunction(meta.settingsFormInitialData)
      ? meta.settingsFormInitialData(staticData)
      : meta.settingsFormInitialData;
    if (meta.hasPrice) {
      initialValues = {...(initialValues || {}), price: 0};
    }
  }

  const handleChangeItemType = (dirty, value) => {
    if (
      newItemType &&
      dirty &&
      // eslint-disable-next-line no-alert
      !confirm('Changing the type will reset this form.')
    ) {
      return;
    }
    // this will force the FinalModalForm to re-render, so we do not need to
    // explicitly `restart()` the form
    setNewItemType(value);
  };

  return (
    <FinalModalForm
      // force re-render since we may need to change form decorators and initial values
      key={editing ? 'edit' : `new-${newItemType}`}
      id="regform-item-settings"
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={initialValues}
      initialValuesEqual={_.isEqual}
      unloadPrompt
      size={meta.settingsModalSize || 'tiny'}
      decorators={meta.settingsFormDecorator ? [meta.settingsFormDecorator] : undefined}
      validate={meta.settingsFormValidator}
      header={
        editing ? (
          <Translate>
            Configure field "<Param name="section" value={itemData.title} />"
          </Translate>
        ) : (
          <>
            <Translate>Add new field</Translate>
            <div style={{float: 'right'}}>
              <FormSpy subscription={{dirty: true}}>
                {({dirty}) => (
                  <ItemTypeDropdown
                    newItemType={newItemType}
                    inModal
                    onClick={value => handleChangeItemType(dirty, value)}
                  />
                )}
              </FormSpy>
            </div>
          </>
        )
      }
    >
      {!editing && !newItemType ? (
        <Message info>
          <Translate>Please choose a field type.</Translate>
        </Message>
      ) : (
        <>
          <FinalInput name="title" label={Translate.string('Title')} required autoFocus />
          <FinalTextArea
            name="description"
            label={Translate.string('Description')}
            description={<Translate>You can use Markdown or basic HTML formatting tags.</Translate>}
          />
          {meta.hasPrice && (
            <FinalInput
              name="price"
              type="number"
              min="0"
              step="0.01"
              validate={v.min(0)}
              parse={val => p.number(val, true, 0)}
              label={Translate.string('Price')}
            />
          )}
          {!meta.noRequired && (
            <FinalCheckbox
              name="isRequired"
              label={Translate.string('Required field')}
              disabled={fieldIsRequired}
            />
          )}
          {SettingsComponent && <SettingsComponent {...itemData} />}
          {isUnsupportedField && (
            <Message visible warning>
              Unknown input type: {inputType}.<br />
              Saving changes will most likely fail or result in some settings being lost.
            </Message>
          )}
        </>
      )}
    </FinalModalForm>
  );
}

ItemSettingsModal.propTypes = {
  id: PropTypes.number,
  sectionId: PropTypes.number,
  defaultNewItemType: PropTypes.string,
  onClose: PropTypes.func.isRequired,
};

ItemSettingsModal.defaultProps = {
  id: null,
  sectionId: null,
  defaultNewItemType: null,
};
