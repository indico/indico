// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React from 'react';
import {Button} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {SortableWrapper, useSortableItem} from 'indico/react/sortable';

export const choiceShape = {
  id: PropTypes.string.isRequired,
  caption: PropTypes.string.isRequired,
  // XXX are those values always present?
  isEnabled: PropTypes.bool.isRequired,
  isBillable: PropTypes.bool.isRequired,
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
  withExtraSlots: PropTypes.bool,
  forAccommodation: PropTypes.bool,
};

Choices.defaultProps = {
  withExtraSlots: false,
  forAccommodation: false,
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
    <tr ref={itemRef} style={style}>
      <td className="table-sortable-handle" ref={handleRef} />
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
            type="checkbox"
            name="isBillable"
            checked={isBillable}
            onChange={makeOnChange('isBillable')}
            {...fieldProps}
          />
        )}
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
        <>
          <td>
            <input
              type="number"
              name="maxExtraSlots"
              min="0"
              value={maxExtraSlots}
              onChange={makeOnChange('maxExtraSlots')}
              {...fieldProps}
            />
          </td>
          <td>
            <input
              type="checkbox"
              name="extraSlotsPay"
              checked={extraSlotsPay}
              onChange={makeOnChange('extraSlotsPay')}
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
          onChange={makeOnChange('isEnabled')}
          {...fieldProps}
        />
      </td>
      <td className="row-actions">
        {!isNoAccommodation && (
          <a
            className="icon-remove remove-row"
            title={Translate.string('Remove row')}
            onClick={fieldProps.disabled ? undefined : onDelete}
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
