// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Button, Label} from 'semantic-ui-react';

import {FinalDropdown, FinalField, FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form/selectors';

import {PlacesLeft} from './PlacesLeftLabel';

import styles from '../../../styles/regform.module.scss';

function BooleanInputComponent({
  value,
  onChange,
  disabled,
  required,
  price,
  placesLimit,
  placesUsed,
}) {
  const currency = useSelector(getCurrency);
  const makeOnClick = newValue => () => {
    if (value === newValue && !required) {
      onChange('');
    } else {
      onChange(newValue);
    }
  };

  return (
    <div styleName="boolean-field">
      <Button.Group>
        <Button
          type="button"
          active={value === 'yes'}
          disabled={disabled || (placesLimit > 0 && placesUsed >= placesLimit)}
          onClick={makeOnClick('yes')}
        >
          <Translate>Yes</Translate>
        </Button>
        <Button
          type="button"
          active={value === 'no'}
          disabled={disabled}
          onClick={makeOnClick('no')}
        >
          <Translate>No</Translate>
        </Button>
      </Button.Group>
      {!!price && (
        <Label pointing="left" styleName={`price-tag ${value !== 'yes' ? 'greyed' : ''}`}>
          {price.toFixed(2)} {currency}
        </Label>
      )}
      {!!placesLimit && (
        <div style={{marginLeft: '1em'}}>
          <PlacesLeft placesLimit={placesLimit} placesUsed={placesUsed} isEnabled={!disabled} />
        </div>
      )}
    </div>
  );
}

BooleanInputComponent.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  required: PropTypes.bool.isRequired,
  price: PropTypes.number.isRequired,
  placesLimit: PropTypes.number.isRequired,
  placesUsed: PropTypes.number.isRequired,
};

export default function BooleanInput({
  htmlName,
  disabled,
  title,
  isRequired,
  defaultValue,
  price,
  placesLimit,
  placesUsed,
}) {
  return (
    <FinalField
      name={htmlName}
      label={title}
      component={BooleanInputComponent}
      required={isRequired}
      disabled={disabled}
      fieldProps={{className: styles.field}}
      price={price}
      placesLimit={placesLimit}
      placesUsed={placesUsed}
      defaultValue={defaultValue}
    />
  );
}

BooleanInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.string,
  price: PropTypes.number,
  placesLimit: PropTypes.number,
  placesUsed: PropTypes.number,
};

BooleanInput.defaultProps = {
  disabled: false,
  isRequired: false,
  defaultValue: '',
  price: 0,
  placesLimit: 0,
  placesUsed: 0,
};

export function BooleanSettings() {
  const options = [
    {key: 'yes', value: 'yes', text: Translate.string('Yes')},
    {key: 'no', value: 'no', text: Translate.string('No')},
  ];
  return (
    <>
      <FinalInput
        name="placesLimit"
        type="number"
        label={Translate.string('Places limit')}
        placeholder={Translate.string('None')}
        step="1"
        min="1"
        validate={v.optional(v.min(0))}
        parse={val => (val === '' ? 0 : val)}
        format={val => (val === 0 ? '' : val)}
      />
      <FinalDropdown
        name="defaultValue"
        label={Translate.string('Default value')}
        options={options}
        placeholder={Translate.string('None')}
        selection
      />
    </>
  );
}
