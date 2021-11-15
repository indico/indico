// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createDecorator from 'final-form-calculate';
import _ from 'lodash';
import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Field} from 'react-final-form';
import {Button} from 'semantic-ui-react';

import {FinalCheckbox, FinalDropdown, FinalField, parsers as p} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {SortableWrapper, useSortableItem} from 'indico/react/sortable';

import '../../../styles/regform.module.scss';

const choiceShape = {
  id: PropTypes.string.isRequired,
  caption: PropTypes.string.isRequired,
  // XXX are those values always present?
  isEnabled: PropTypes.bool.isRequired,
  isBillable: PropTypes.bool.isRequired,
  price: PropTypes.number.isRequired,
  placesLimit: PropTypes.number.isRequired,
  maxExtraSlots: PropTypes.number.isRequired,
};

export default function InputSingleChoice({
  htmlName,
  disabled,
  isRequired,
  itemType,
  choices,
  defaultItem,
  withExtraSlots,
}) {
  // TODO: billable/price
  // TODO: places left
  // TODO: set value as `{uuid: places}` (when adding final-form integration)
  // TODO: disable options triggering price changes after payment (or warn for managers)
  // TODO: warnings for deleted/modified choices
  const [value, setValue] = useState(defaultItem || '');
  const [slotsUsed, setSlotsUsed] = useState(1);
  const selectedChoice = choices.find(c => c.id === value);

  let extraSlotsDropdown = null;
  if (withExtraSlots && selectedChoice && selectedChoice.maxExtraSlots > 0) {
    extraSlotsDropdown = (
      <select
        name={`${htmlName}-extra`}
        disabled={disabled}
        value={slotsUsed}
        onChange={evt => setSlotsUsed(evt.target.value)}
      >
        {_.range(1, selectedChoice.maxExtraSlots + 2).map(i => (
          <option key={i} value={i}>
            {i}
          </option>
        ))}
      </select>
    );
  }

  const handleChange = evt => {
    setValue(evt.target.value);
    setSlotsUsed(1);
  };

  if (itemType === 'dropdown') {
    return (
      <>
        <select name={htmlName} disabled={disabled} value={value} onChange={handleChange}>
          <option key="" value="">
            {Translate.string('Choose an option')}
          </option>
          {choices.map(c => (
            <option key={c.id} value={c.id} disabled={!c.isEnabled}>
              {c.caption}
            </option>
          ))}
        </select>
        {extraSlotsDropdown}
      </>
    );
  } else if (itemType === 'radiogroup') {
    const radioChoices = [...choices];
    if (!isRequired) {
      radioChoices.unshift({id: '', isEnabled: true, caption: Translate.string('None')});
    }
    return (
      <>
        <ul styleName="radio-group">
          {radioChoices.map(c => (
            <li key={c.id}>
              <input
                type="radio"
                name={htmlName}
                id={`${htmlName}-${c.id}`}
                value={c.id}
                disabled={!c.isEnabled}
                checked={c.id === value}
                onChange={handleChange}
              />{' '}
              <label htmlFor={`${htmlName}-${c.id}`}>{c.caption}</label>
            </li>
          ))}
        </ul>
        {extraSlotsDropdown}
      </>
    );
  } else {
    // XXX can this happen?! maybe make sure we always have a value!
    return `ERROR: Unknown type ${itemType}`;
  }
}

InputSingleChoice.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  itemType: PropTypes.oneOf(['dropdown', 'radiogroup']).isRequired,
  defaultItem: PropTypes.string,
  withExtraSlots: PropTypes.bool,
  // TODO: placesUsed, captions - only needed once we deal with real data
};

InputSingleChoice.defaultProps = {
  disabled: false,
  defaultItem: null,
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
        selectOnNavigation={false}
        selectOnBlur={false}
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
            selectOnNavigation={false}
            selectOnBlur={false}
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

function Choices({onFocus, onBlur, onChange, disabled, value, withExtraSlots}) {
  const makeOnDelete = id => () => onChange(value.filter(choice => choice.id !== id));
  const makeOnChange = id => (field, val) =>
    onChange(value.map(choice => (choice.id !== id ? choice : {...choice, [field]: val})));
  const handleMove = (sourceIndex, targetIndex) => {
    const newValue = [...value];
    const sourceItem = newValue[sourceIndex];
    newValue.splice(sourceIndex, 1);
    newValue.splice(targetIndex, 0, sourceItem);
    onChange(newValue);
  };
  const handleAdd = () => {
    const newItem = {
      id: `new:${nanoid()}`,
      caption: '',
      isEnabled: true,
      isBillable: false,
      price: 0,
      placesLimit: 0,
      maxExtraSlots: 0,
    };
    onChange([...value, newItem]);
  };

  // TODO: style this nicely, ideally ditch the table and find a better way to do this
  // one option could be showing just the text and settings (icons?), and using a more
  // explicit edit action on the individual entries (which could then use a modal to
  // edit  the actual data)
  return (
    <>
      <SortableWrapper accept="regform-item-choice">
        <table className="regform-table">
          <thead>
            <tr>
              <th style={{width: '1.75em'}} />
              <th>
                <Translate>Caption</Translate>
              </th>
              <th>
                <Translate>Billable</Translate>
              </th>
              <th style={{width: '7em'}}>
                <Translate>Price</Translate>
              </th>
              <th style={{width: '7em'}}>
                <Translate>Limit</Translate>
              </th>
              {withExtraSlots && (
                <>
                  <th>
                    <Translate>Max. extra slots</Translate>
                  </th>
                  <th>
                    <Translate>Extra slots pay</Translate>
                  </th>
                </>
              )}
              <th>
                <Translate>Enabled</Translate>
              </th>
              <th />
            </tr>
          </thead>
          <tbody>
            {value.map((c, i) => (
              <Choice
                key={c.id}
                index={i}
                withExtraSlots={withExtraSlots}
                onChange={makeOnChange(c.id)}
                onDelete={makeOnDelete(c.id)}
                onMove={handleMove}
                fieldProps={{onFocus, onBlur, disabled}}
                {...c}
              />
            ))}
          </tbody>
        </table>
      </SortableWrapper>
      <Button type="button" onClick={handleAdd} disabled={disabled}>
        <Translate>Add new</Translate>
      </Button>
    </>
  );
}

Choices.propTypes = {
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  value: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  disabled: PropTypes.bool.isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
};

function Choice({
  withExtraSlots,
  fieldProps,
  index,
  id,
  caption,
  isBillable,
  price,
  placesLimit,
  maxExtraSlots,
  extraSlotsPay,
  isEnabled,
  onChange,
  onMove,
  onDelete,
}) {
  const [handleRef, itemRef, style] = useSortableItem({
    type: 'regform-item-choice',
    id,
    index,
    active: !fieldProps.disabled,
    separateHandle: true,
    moveItem: onMove,
    // nothing to do since we don't need to "save" at the end
    onDrop: () => null,
  });

  const makeOnChange = (field, checkbox = false, number = false) => evt => {
    const elem = evt.target;
    if (checkbox) {
      onChange(field, elem.checked);
    } else if (number) {
      onChange(field, +elem.value);
    } else {
      onChange(field, elem.value);
    }
  };

  return (
    <tr ref={itemRef} style={style}>
      <td className="table-sortable-handle" ref={handleRef} />
      <td>
        <input
          type="text"
          name="caption"
          value={caption}
          required
          onChange={makeOnChange('caption')}
        />
      </td>
      <td>
        <input
          type="checkbox"
          name="isBillable"
          checked={isBillable}
          onChange={makeOnChange('isBillable', true)}
          {...fieldProps}
        />
      </td>
      <td>
        <input
          type="number"
          name="price"
          min="0"
          step="0.01"
          value={price || ''}
          onChange={makeOnChange('price', false, true)}
          {...fieldProps}
        />
      </td>
      <td>
        <input
          type="number"
          name="placesLimit"
          min="0"
          value={placesLimit || ''}
          onChange={makeOnChange('placesLimit', false, true)}
          {...fieldProps}
        />
      </td>
      {withExtraSlots && (
        <>
          <td>
            <input
              type="number"
              name="maxExtraSlots"
              min="0"
              value={maxExtraSlots}
              onChange={makeOnChange('maxExtraSlots', false, true)}
              {...fieldProps}
            />
          </td>
          <td>
            <input
              type="checkbox"
              name="extraSlotsPay"
              checked={extraSlotsPay}
              onChange={makeOnChange('extraSlotsPay', true)}
              {...fieldProps}
            />
          </td>
        </>
      )}
      <td>
        <input
          type="checkbox"
          name="enabled"
          checked={isEnabled}
          onChange={makeOnChange('isEnabled', true)}
          {...fieldProps}
        />
      </td>
      <td className="row-actions">
        <a
          className="icon-remove remove-row"
          title={Translate.string('Remove row')}
          onClick={fieldProps.disabled ? undefined : onDelete}
        />
      </td>
    </tr>
  );
}

Choice.propTypes = {
  withExtraSlots: PropTypes.bool.isRequired,
  fieldProps: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  onMove: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  ...choiceShape,
};
