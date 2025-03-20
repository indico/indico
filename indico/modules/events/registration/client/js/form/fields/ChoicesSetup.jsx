// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createDecorator from 'final-form-calculate';
import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Input, Button} from 'semantic-ui-react';

import {ItemListField} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form/selectors';

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

  const itemShape = [
    {
      name: 'caption',
      title: Translate.string('Caption'),
      fieldProps: item => ({
        placeholder: item.isNoAccommodation ? Translate.string('No accommodation') : undefined,
      }),
    },
    {
      name: 'price',
      title: Translate.string('Price ({currency})', {currency}),
      width: '7em',
      defaultValue: 0,
      render: item => !item.isNoAccommodation,
      fieldProps: {type: 'number', min: 0, step: 0.01},
    },
    {
      name: 'placesLimit',
      title: Translate.string('Limit'),
      width: '7em',
      defaultValue: 0,
      render: item => !item.isNoAccommodation,
      fieldProps: {type: 'number', min: 0},
    },
  ];
  if (withExtraSlots) {
    itemShape.push({
      name: 'maxExtraSlots',
      title: Translate.string('Max. extra slots'),
      width: '9em',
      as: Input,
      defaultValue: 0,
      render: item => !item.isNoAccommodation,
      fieldProps: (item, onItemChange) => ({
        type: 'number',
        min: 0,
        icon: {
          name: 'dollar',
          link: true,
          color: item.extraSlotsPay ? 'blue' : 'grey',
          title: Translate.string('Extra slots pay'),
          onClick: () => onItemChange('extraSlotsPay', !item.extraSlotsPay),
        },
        style: {width: '7.5em'},
      }),
    });
  }

  return (
    <>
      <ItemListField
        value={value}
        onChange={onChange}
        itemShape={itemShape}
        disabled={disabled}
        canRemoveItem={item => !item.isNoAccommodation}
        onFocus={onFocus}
        onBlur={onBlur}
        canDisableItem
        sortable
        scrollable
      />
      {forAccommodation && (
        <p
          className="field-description"
          style={{textAlign: 'end', marginTop: '-1em', marginBottom: '1em'}}
        >
          <Translate>All prices are per night</Translate>
        </p>
      )}
      {/* eslint-disable-next-line no-undef */}
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
