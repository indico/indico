// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormSpy} from 'react-final-form';
import {useSelector, useDispatch} from 'react-redux';
import {Dropdown, Message} from 'semantic-ui-react';

import {FinalCheckbox, FinalInput, FinalTextArea, getValuesForFields} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate, Param} from 'indico/react/i18n';

import {fieldRegistry} from '../form/fields/registry';

import * as actions from './actions';
import {getStaticData, getItemById} from './selectors';

import '../../styles/regform.module.scss';

const newItemTypeOptions = Object.entries(fieldRegistry).map(([name, {title}]) => ({
  key: name,
  value: name,
  text: title,
}));

export default function ItemSettingsModal({id, sectionId, onClose}) {
  const dispatch = useDispatch();
  const [newItemType, setNewItemType] = useState(null);
  const editing = id !== null;
  const staticData = useSelector(getStaticData);
  const {inputType: existingInputType, fieldIsRequired, ...itemData} = useSelector(state =>
    editing ? getItemById(state, id) : {}
  );
  const inputType = editing ? existingInputType : newItemType;
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
  }

  return (
    <FinalModalForm
      // force re-render since we may need to change form decorators and initial values
      key={editing ? 'edit' : `new-${newItemType}`}
      id="regform-item-settings"
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={initialValues}
      initialValuesEqual={_.isEqual}
      alignTop
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
                  <Dropdown
                    defaultOpen={!editing && !newItemType}
                    selectOnNavigation={false}
                    selectOnBlur={false}
                    value={newItemType}
                    onChange={(__, {value}) => {
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
                    }}
                    text={
                      newItemType
                        ? fieldRegistry[newItemType].title
                        : Translate.string('Choose type')
                    }
                    options={newItemTypeOptions}
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
  onClose: PropTypes.func.isRequired,
};

ItemSettingsModal.defaultProps = {
  id: null,
  sectionId: null,
};
