// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createDecorator from 'final-form-calculate';
import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Button, Input} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';
import {SortableWrapper, useSortableItem} from 'indico/react/sortable';

import {getCurrency} from '../../form/selectors';

import './ChoicesSetup.module.scss';

export const choiceShape = {
  id: PropTypes.string.isRequired,
  caption: PropTypes.string.isRequired,
  // XXX are those values always present?
  isEnabled: PropTypes.bool.isRequired,
  price: PropTypes.number.isRequired,
  placesLimit: PropTypes.number,
  maxExtraSlots: PropTypes.number,
};

export function Choices({
  onFocus,
  onBlur,
  onChange,
  disabled,
  value,
  withExtraSlots,
  forAccommodation,
}) {
  const currency = useSelector(getCurrency);
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
      price: 0,
      placesLimit: 0,
    };
    if (!forAccommodation) {
      newItem.maxExtraSlots = 0;
    }
    onChange([...value, newItem]);
  };

  // TODO: style this nicely, ideally ditch the table and find a better way to do this
  // one option could be showing just the text and settings (icons?), and using a more
  // explicit edit action on the individual entries (which could then use a modal to
  // edit  the actual data)
  return (
    <>
      <SortableWrapper styleName="choices-table-wrapper" accept="regform-item-choice">
        <table styleName="choices-table">
          <thead>
            <tr>
              <th style={{width: '1.75em'}} />
              <th>
                <Translate>Caption</Translate>
              </th>
              <th style={{width: '7em'}}>
                <Translate>
                  Price (<Param name="currency" value={currency} />)
                </Translate>
              </th>
              <th style={{width: '7em'}}>
                <Translate>Limit</Translate>
              </th>
              {withExtraSlots ? (
                <th colSpan="2">
                  <Translate>Max. extra slots</Translate>
                </th>
              ) : (
                <th style={{width: '3.7em'}} />
              )}
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
      {forAccommodation && (
        <p
          className="field-description"
          style={{textAlign: 'end', marginTop: '-1em', marginBottom: '1em'}}
        >
          <Translate>All prices are per night</Translate>
        </p>
      )}
      <Button type="button" onClick={handleAdd} disabled={disabled}>
        <Translate context="Choice">Add new</Translate>
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
  withExtraSlots: PropTypes.bool,
  forAccommodation: PropTypes.bool,
};

Choices.defaultProps = {
  withExtraSlots: false,
  forAccommodation: false,
};

export const choiceFieldsSettingsFormDecorator = createDecorator({
  field: 'choices',
  updates: choices => ({isPriceSet: choices.some(c => c.price)}),
});

function Choice({
  withExtraSlots,
  fieldProps,
  index,
  id,
  caption,
  price,
  placesLimit,
  maxExtraSlots,
  extraSlotsPay,
  isEnabled,
  isNoAccommodation,
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

  const makeOnChange = field => evt => {
    const elem = evt.target;
    if (elem.type === 'checkbox') {
      onChange(field, elem.checked);
    } else if (elem.type === 'number') {
      onChange(field, +elem.value);
    } else {
      onChange(field, elem.value);
    }
  };

  return (
    <tr ref={itemRef} style={style} styleName={!isEnabled ? 'disabled-row' : undefined}>
      <td styleName="table-sortable-handle" ref={handleRef} />
      <td>
        <input
          type="text"
          name="caption"
          value={caption}
          required
          onChange={makeOnChange('caption')}
          placeholder={isNoAccommodation ? Translate.string('No accommodation') : undefined}
        />
      </td>
      <td>
        {!isNoAccommodation && (
          <input
            type="number"
            name="price"
            min="0"
            step="0.01"
            value={price || ''}
            onChange={makeOnChange('price')}
            {...fieldProps}
          />
        )}
      </td>
      <td>
        {!isNoAccommodation && (
          <input
            type="number"
            name="placesLimit"
            min="0"
            value={placesLimit || ''}
            onChange={makeOnChange('placesLimit')}
            {...fieldProps}
          />
        )}
      </td>
      {!isNoAccommodation && withExtraSlots && (
        <td style={{width: 0}}>
          <Input
            type="number"
            name="maxExtraSlots"
            min="0"
            value={maxExtraSlots}
            onChange={makeOnChange('maxExtraSlots')}
            icon={{
              name: 'dollar',
              link: true,
              color: extraSlotsPay ? 'blue' : 'grey',
              title: Translate.string('Extra slots pay'),
              onClick: () => onChange('extraSlotsPay', !extraSlotsPay),
            }}
            style={{width: '7.5em'}}
            {...fieldProps}
          />
        </td>
      )}
      <td style={{textAlign: 'end'}}>
        {!isNoAccommodation && (
          <a
            className="icon-remove remove-row"
            title={Translate.string('Remove row')}
            onClick={fieldProps.disabled ? undefined : onDelete}
          />
        )}
        {isEnabled ? (
          <a
            className="icon-disable"
            title={Translate.string('Disable choice')}
            onClick={() => onChange('isEnabled', false)}
          />
        ) : (
          <a
            className="icon-checkmark remove-row"
            title={Translate.string('Enable choice')}
            onClick={() => onChange('isEnabled', true)}
          />
        )}
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
