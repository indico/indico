// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormSpy} from 'react-final-form';
import {useSelector, useDispatch} from 'react-redux';
import {Icon, Message} from 'semantic-ui-react';

import {
  FinalCheckbox,
  FinalInput,
  FinalTextArea,
  getValuesForFields,
  validators as v,
  parsers as p,
} from 'indico/react/forms';
import {Fieldset} from 'indico/react/forms/fields';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate, Param, PluralTranslate} from 'indico/react/i18n';
import {renderPluginComponents} from 'indico/utils/plugins';

import {getFieldRegistry} from '../form/fields/registry';
import {ShowIfInput} from '../form/fields/ShowIfInput';
import {getStaticData, getItemById} from '../form/selectors';

import * as actions from './actions';
import ItemTypeDropdown from './ItemTypeDropdown';
import {getDataRetentionRange} from './selectors';

const EMPTY_DATA = {}; // avoid new object on every selector call since this triggers a warning

export default function ItemSettingsModal({id, sectionId, defaultNewItemType, onClose}) {
  const dispatch = useDispatch();
  const [newItemType, setNewItemType] = useState(defaultNewItemType);
  const editing = id !== null;
  const staticData = useSelector(getStaticData);
  const dataRetentionRange = useSelector(getDataRetentionRange);
  const {inputType: existingInputType, fieldIsRequired, ...itemData} = useSelector(state =>
    editing ? getItemById(state, id) : EMPTY_DATA
  );
  const inputType = editing ? existingInputType : newItemType;
  const fieldRegistry = getFieldRegistry();
  const isUnsupportedField = !(inputType in fieldRegistry);
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
      decorators={meta.settingsFormDecorators ? meta.settingsFormDecorators : undefined}
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
            description={<Translate>You may use Markdown for formatting.</Translate>}
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
          {renderPluginComponents(`regform-${inputType}-field-settings`, {...itemData})}
          {!fieldIsRequired && <ShowIfInput fieldId={id} />}
          {!meta.noRetentionPeriod && !fieldIsRequired && (
            <Fieldset legend={Translate.string('Privacy')} compact>
              <FinalInput
                name="retentionPeriod"
                type="number"
                placeholder={
                  dataRetentionRange.regform
                    ? String(dataRetentionRange.regform)
                    : Translate.string('Indefinite')
                }
                step="1"
                min={dataRetentionRange.min}
                max={dataRetentionRange.max}
                validate={v.optional(v.range(dataRetentionRange.min, dataRetentionRange.max))}
                label={Translate.string('Retention period (weeks)')}
                description={
                  dataRetentionRange.regform
                    ? Translate.string(
                        'Since the registration form has a limited retention period ({period}), ' +
                          'data in this field is automatically deleted after that period. ' +
                          'However, you can set a shorter duration here.',
                        {
                          period: PluralTranslate.string(
                            '{n} week',
                            '{n} weeks',
                            dataRetentionRange.regform,
                            {
                              n: dataRetentionRange.regform,
                            }
                          ),
                        }
                      )
                    : Translate.string(
                        'Specify how long user-provided data for this field will be preserved.'
                      )
                }
              />
              <FormSpy subscription={{values: true}}>
                {({values}) =>
                  (!!values.price || values.isPriceSet) && !!values.retentionPeriod ? (
                    <Message visible icon warning>
                      <Icon name="warning" />
                      <Message.Content>
                        <Translate>
                          Please note that invoice information will be lost as well once a field's
                          retention period expires.
                        </Translate>
                      </Message.Content>
                    </Message>
                  ) : (
                    ''
                  )
                }
              </FormSpy>
            </Fieldset>
          )}
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
