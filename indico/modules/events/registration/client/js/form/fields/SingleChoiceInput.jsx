// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createDecorator from 'final-form-calculate';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Form, Label, Dropdown} from 'semantic-ui-react';

import {RadioButton, Select} from 'indico/react/components';
import {FinalCheckbox, FinalDropdown, FinalField, parsers as p} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';

import {getPriceFormatter} from '../../form/selectors';
import {getFieldValue, getManagement, getPaid} from '../../form_submission/selectors';

import ChoiceLabel from './ChoiceLabel';
import {Choices, choiceShape} from './ChoicesSetup';
import {PlacesLeft} from './PlacesLeftLabel';

import '../../../styles/regform.module.scss';
import './table.module.scss';

function SingleChoiceDropdown({
  id,
  existingValue,
  value,
  onChange,
  onFocus,
  onBlur,
  disabled,
  isRequired,
  isPurged,
  choices,
  withExtraSlots,
  placesUsed,
}) {
  const paid = useSelector(getPaid);
  const management = useSelector(getManagement);
  const formatPrice = useSelector(getPriceFormatter);
  const selectedChoice = choices.find(c => c.id in value) || {};
  const selectedSeats = value[selectedChoice.id] || 0;

  const isPaidChoice = choice => choice.price > 0 && paid;
  const isPaidChoiceLocked = choice => !management && isPaidChoice(choice);

  let extraSlotsDropdown = null;
  const extraSlotsLabelId = `${id}-label`;
  const shouldShowExtraSlots = withExtraSlots && selectedChoice && selectedChoice.maxExtraSlots > 0;
  const shouldShowExtraSlotsLabel = shouldShowExtraSlots && !!selectedChoice.price;

  if (shouldShowExtraSlots) {
    const slotValues = _.range(1, selectedChoice.maxExtraSlots + 2);
    const options = slotValues.map(i => ({
      value: i,
      disabled:
        selectedChoice.placesLimit > 0 &&
        (placesUsed[selectedChoice.id] || 0) - (existingValue[selectedChoice.id] || 0) + i >
          selectedChoice.placesLimit,
    }));
    const comboBoxExtraProps = {};
    if (shouldShowExtraSlotsLabel) {
      comboBoxExtraProps['aria-describedby'] = extraSlotsLabelId;
    }
    extraSlotsDropdown = (
      <Select
        id={id ? `${id}-extraslots` : ''}
        options={options}
        disabled={
          disabled ||
          isPaidChoiceLocked(selectedChoice) ||
          (selectedChoice.placesLimit > 0 &&
            (placesUsed[selectedChoice.id] || 0) - (existingValue[selectedChoice.id] || 0) >=
              selectedChoice.placesLimit)
        }
        value={String(selectedSeats)}
        onChange={evt => {
          const selectedSlots = Number(evt.target.value);
          onChange({[selectedChoice.id]: selectedSlots});
        }}
        aria-label={Translate.string('Select extra slots')}
        required
        {...comboBoxExtraProps}
      />
    );
  }

  const options = choices.map(choice => ({
    value: choice.id,
    label: (
      <div styleName="dropdown-text" key={choice.id}>
        <div styleName="caption" data-label>
          <ChoiceLabel choice={choice} management={management} paid={isPaidChoice(choice)} />
        </div>
        <div styleName="labels">
          {!!choice.price && <Label>{formatPrice(choice.price)}</Label>}
          {choice.placesLimit === 0 ? null : (
            <PlacesLeft
              placesLimit={choice.placesLimit}
              placesUsed={placesUsed[choice.id] || 0}
              isEnabled={choice.isEnabled}
            />
          )}
        </div>
      </div>
    ),
    disabled:
      !choice.isEnabled ||
      isPaidChoiceLocked(choice) ||
      (choice.placesLimit > 0 &&
        (placesUsed[choice.id] || 0) >= choice.placesLimit &&
        !existingValue[choice.id]),
  }));

  const handleChange = evt => {
    if (!evt.target.value) {
      onChange({});
      return;
    }
    onChange({[evt.target.value]: 1});
  };

  return (
    <Form.Group styleName="single-choice-dropdown">
      <Form.Field>
        <Select
          id={id}
          onChange={handleChange}
          options={options}
          value={(!isPurged && selectedChoice.id) || ''}
          required={isRequired}
          disabled={disabled}
          onFocus={onFocus}
          onBlur={onBlur}
        />
      </Form.Field>
      <div styleName="extra-slots">
        {extraSlotsDropdown}
        {shouldShowExtraSlotsLabel && (
          <Label pointing="left" id={extraSlotsLabelId}>
            <Translate>
              Total:{' '}
              <Param
                name="price"
                value={formatPrice(
                  (selectedChoice.extraSlotsPay ? selectedSeats : 1) * selectedChoice.price
                )}
              />
            </Translate>
          </Label>
        )}
      </div>
    </Form.Group>
  );
}

SingleChoiceDropdown.propTypes = {
  id: PropTypes.string.isRequired,
  value: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  isRequired: PropTypes.bool.isRequired,
  isPurged: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
  existingValue: PropTypes.objectOf(PropTypes.number).isRequired,
};

function SingleChoiceRadioGroup({
  id,
  existingValue,
  value,
  onChange,
  disabled,
  isRequired,
  isPurged,
  choices,
  withExtraSlots,
  placesUsed,
}) {
  const paid = useSelector(getPaid);
  const management = useSelector(getManagement);
  const formatPrice = useSelector(getPriceFormatter);
  const selectedChoice = choices.find(c => c.id in value) || {id: ''};
  const selectedSeats = value[selectedChoice.id] || 0;
  const radioChoices = [...choices];
  if (!isRequired) {
    radioChoices.unshift({id: '', isEnabled: true, caption: Translate.string('None', 'Choice')});
  }

  const handleChange = newValue => {
    if (newValue === '') {
      onChange({});
    } else {
      onChange({[newValue]: 1});
    }
  };

  const isChecked = currentChoice => currentChoice.id === selectedChoice.id;

  const isPaidChoice = choice => choice.price > 0 && paid;
  const isPaidChoiceLocked = choice => !management && isPaidChoice(choice);

  return (
    <table styleName="choice-table" role="presentation">
      <tbody>
        {radioChoices.map((c, index) => {
          return (
            <tr key={c.id} styleName="row">
              <td>
                <RadioButton
                  id={id ? `${id}-${index}` : ''}
                  name={id}
                  label={<ChoiceLabel choice={c} management={management} paid={isPaidChoice(c)} />}
                  key={c.id}
                  value={c.id}
                  disabled={
                    !c.isEnabled ||
                    disabled ||
                    isPaidChoiceLocked(c) ||
                    (c.placesLimit > 0 &&
                      (placesUsed[c.id] || 0) - (existingValue[c.id] || 0) >= c.placesLimit)
                  }
                  checked={!isPurged && isChecked(c)}
                  onChange={() => handleChange(c.id)}
                />
              </td>
              <td>
                {c.isEnabled && !!c.price && (
                  <Label pointing="left" styleName={isPurged || !isChecked(c) ? 'greyed' : ''}>
                    {formatPrice(c.price)}
                  </Label>
                )}
              </td>
              <td>
                {c.id !== '' && c.placesLimit !== 0 && (
                  <PlacesLeft
                    placesLimit={c.placesLimit}
                    placesUsed={placesUsed[c.id] || 0}
                    isEnabled={!disabled && c.isEnabled && !isPaidChoiceLocked(c)}
                  />
                )}
              </td>
              {withExtraSlots && !!c.maxExtraSlots && selectedChoice.id === c.id && (
                <>
                  <td>
                    {c.isEnabled && (
                      <Dropdown
                        id={id ? `${id}-extraslot` : ''}
                        selection
                        styleName="dropdown"
                        disabled={
                          disabled ||
                          isPaidChoiceLocked(c) ||
                          (c.placesLimit > 0 &&
                            (placesUsed[c.id] || 0) - (existingValue[c.id] || 0) >= c.placesLimit)
                        }
                        value={selectedSeats}
                        onChange={(e, data) => onChange({[selectedChoice.id]: data.value})}
                        options={_.range(1, c.maxExtraSlots + 2).map(i => ({
                          key: i,
                          value: i,
                          text: i,
                          disabled:
                            selectedChoice.placesLimit > 0 &&
                            (placesUsed[selectedChoice.id] || 0) -
                              (existingValue[selectedChoice.id] || 0) +
                              i >
                              selectedChoice.placesLimit,
                        }))}
                      />
                    )}
                  </td>
                  <td>
                    {c.isEnabled && !!c.price && (
                      <Label pointing="left">
                        <Translate>
                          Total:{' '}
                          <Param
                            name="price"
                            value={formatPrice(
                              (selectedChoice.extraSlotsPay ? selectedSeats : 1) * c.price
                            )}
                          />
                        </Translate>
                      </Label>
                    )}
                  </td>
                </>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

SingleChoiceRadioGroup.propTypes = {
  id: PropTypes.string.isRequired,
  value: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  isRequired: PropTypes.bool.isRequired,
  isPurged: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
  existingValue: PropTypes.objectOf(PropTypes.number).isRequired,
};

function SingleChoiceInputComponent({
  id,
  existingValue,
  value,
  onChange,
  onFocus,
  onBlur,
  disabled,
  isRequired,
  isPurged,
  itemType,
  choices,
  withExtraSlots,
  placesUsed,
}) {
  let component = null;
  if (itemType === 'dropdown') {
    component = (
      <SingleChoiceDropdown
        id={id}
        value={value}
        existingValue={existingValue}
        onChange={onChange}
        onFocus={onFocus}
        onBlur={onBlur}
        disabled={disabled}
        isRequired={isRequired}
        isPurged={isPurged}
        choices={choices}
        withExtraSlots={withExtraSlots}
        placesUsed={placesUsed}
      />
    );
  } else if (itemType === 'radiogroup') {
    component = (
      <SingleChoiceRadioGroup
        id={id}
        value={value}
        existingValue={existingValue}
        onChange={onChange}
        disabled={disabled}
        isRequired={isRequired}
        isPurged={isPurged}
        choices={choices}
        withExtraSlots={withExtraSlots}
        placesUsed={placesUsed}
      />
    );
  } else {
    return `ERROR: Unknown type ${itemType}`;
  }

  return component;
}

SingleChoiceInputComponent.propTypes = {
  id: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
  isRequired: PropTypes.bool.isRequired,
  isPurged: PropTypes.bool.isRequired,
  itemType: PropTypes.oneOf(['dropdown', 'radiogroup']).isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
  existingValue: PropTypes.objectOf(PropTypes.number).isRequired,
};

export default function SingleChoiceInput({
  fieldId,
  htmlId,
  htmlName,
  disabled,
  isRequired,
  isPurged,
  itemType,
  choices,
  withExtraSlots,
  placesUsed,
}) {
  const existingValue = useSelector(state => getFieldValue(state, fieldId)) || {};

  function validate(value) {
    const noValue = !value || !Object.keys(value).length;
    if (isRequired && noValue) {
      return Translate.string('This field is required');
    }

    if (noValue) {
      // When there is no value but the field is not required, it's a pass
      return;
    }
  }

  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={SingleChoiceInputComponent}
      format={v => v || {}}
      required={isRequired}
      isRequired={isRequired}
      validate={validate}
      disabled={disabled}
      isPurged={isPurged}
      itemType={itemType}
      choices={choices}
      withExtraSlots={withExtraSlots}
      placesUsed={placesUsed}
      existingValue={existingValue}
      isEqual={_.isEqual}
    />
  );
}

SingleChoiceInput.propTypes = {
  fieldId: PropTypes.number.isRequired,
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  isPurged: PropTypes.bool.isRequired,
  itemType: PropTypes.oneOf(['dropdown', 'radiogroup']).isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
};

SingleChoiceInput.defaultProps = {
  disabled: false,
  isRequired: false,
  withExtraSlots: false,
};

export const singleChoiceSettingsFormDecorator = createDecorator({
  field: 'choices',
  updates: (choices, __, {defaultItem}) => {
    // clear the default item when it's removed from the choices or disabled
    if (!choices.some(c => c.id === defaultItem && c.isEnabled)) {
      return {defaultItem: null};
    }
    return {};
  },
});

export const singleChoiceSettingsInitialData = {
  choices: [],
  itemType: 'dropdown',
  defaultItem: null,
  withExtraSlots: false,
};

export function SingleChoiceSettings() {
  return (
    <>
      <FinalDropdown
        name="itemType"
        label={Translate.string('Widget type')}
        options={[
          {key: 'dropdown', value: 'dropdown', text: Translate.string('Drop-down list')},
          {key: 'radiogroup', value: 'radiogroup', text: Translate.string('Radio buttons')},
        ]}
        selection
        required
      />
      <Field name="choices" subscription={{value: true}} isEqual={_.isEqual}>
        {({input: {value: choices}}) => (
          <FinalDropdown
            name="defaultItem"
            label={Translate.string('Default option')}
            options={choices
              .filter(c => c.isEnabled)
              .map(c => ({key: c.id, value: c.id, text: c.caption}))}
            disabled={!choices.some(c => c.isEnabled)}
            parse={p.nullIfEmpty}
            selection
          />
        )}
      </Field>
      <FinalCheckbox name="withExtraSlots" label={Translate.string('Enable extra slots')} />
      <Field name="withExtraSlots" subscription={{value: true}}>
        {({input: {value: withExtraSlots}}) => (
          <FinalField
            name="choices"
            label={Translate.string('Choices')}
            component={Choices}
            withExtraSlots={withExtraSlots}
            isEqual={_.isEqual}
            required
          />
        )}
      </Field>
    </>
  );
}
