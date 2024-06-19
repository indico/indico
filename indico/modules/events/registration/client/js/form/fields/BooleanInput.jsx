// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
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
import {getFieldValue} from '../../form_submission/selectors';

import {PlacesLeft} from './PlacesLeftLabel';

import '../../../styles/regform.module.scss';

function BooleanInputComponent({
  fieldId,
  value,
  onChange,
  disabled,
  required,
  isPurged,
  price,
  placesLimit,
  placesUsed,
}) {
  const currency = useSelector(getCurrency);
  const existingValue = useSelector(state => getFieldValue(state, fieldId));

  const makeOnClick = newValue => () => {
    if (value === newValue && !required) {
      onChange(null);
    } else {
      onChange(newValue);
    }
  };

  return (
    <div styleName="boolean-field">
      <Button.Group>
        <Button
          type="button"
          active={!isPurged && value === true}
          disabled={disabled || (placesLimit > 0 && placesUsed >= placesLimit && !existingValue)}
          onClick={makeOnClick(true)}
        >
          <Translate>Yes</Translate>
        </Button>
        <Button
          type="button"
          active={!isPurged && value === false}
          disabled={disabled}
          onClick={makeOnClick(false)}
        >
          <Translate>No</Translate>
        </Button>
      </Button.Group>
      {!!price && (
        <Label pointing="left" styleName={`price-tag ${value !== true ? 'greyed' : ''}`}>
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
  fieldId: PropTypes.number.isRequired,
  value: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  required: PropTypes.bool.isRequired,
  isPurged: PropTypes.bool.isRequired,
  price: PropTypes.number.isRequired,
  placesLimit: PropTypes.number.isRequired,
  placesUsed: PropTypes.number.isRequired,
};

BooleanInputComponent.defaultProps = {
  value: null,
};

export default function BooleanInput({
  fieldId,
  htmlName,
  disabled,
  isRequired,
  isPurged,
  price,
  placesLimit,
  placesUsed,
}) {
  const validateBoolean = value => {
    if (isRequired && value === null) {
      return Translate.string('This field is required.');
    }
  };

  return (
    <FinalField
      fieldId={fieldId}
      name={htmlName}
      component={BooleanInputComponent}
      required={isRequired ? 'no-validator' : isRequired}
      validate={validateBoolean}
      disabled={disabled}
      isPurged={isPurged}
      allowNull
      price={price}
      placesLimit={placesLimit}
      placesUsed={placesUsed}
    />
  );
}

BooleanInput.propTypes = {
  fieldId: PropTypes.number.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  isPurged: PropTypes.bool.isRequired,
  price: PropTypes.number,
  placesLimit: PropTypes.number,
  placesUsed: PropTypes.number,
};

BooleanInput.defaultProps = {
  disabled: false,
  isRequired: false,
  price: 0,
  placesLimit: 0,
  placesUsed: 0,
};

export function BooleanSettings() {
  const options = [
    {key: true, value: true, text: Translate.string('Yes')},
    {key: false, value: false, text: Translate.string('No')},
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
        parse={val => (val === '' ? 0 : +val)}
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
