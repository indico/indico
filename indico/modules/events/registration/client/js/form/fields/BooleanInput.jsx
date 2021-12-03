// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import {Button, Form, Label} from 'semantic-ui-react';

import {FinalDropdown, FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

import {PlacesLeft} from './PlacesLeftLabel';

import '../../../styles/regform.module.scss';

export default function BooleanInput({
  disabled,
  title,
  isRequired,
  defaultValue,
  price,
  placesLimit,
}) {
  const [value, setValue] = useState(defaultValue);
  const currency = useSelector(getCurrency);
  const makeOnClick = newValue => () => {
    if (value === newValue && !isRequired) {
      setValue('');
    } else {
      setValue(newValue);
    }
  };

  return (
    <Form.Field required={isRequired} disabled={disabled} styleName="field">
      <label>{title}</label>
      <div styleName="boolean-field">
        <Button.Group>
          <Button active={value === 'yes'} onClick={makeOnClick('yes')}>
            <Translate>Yes</Translate>
          </Button>
          <Button active={value === 'no'} onClick={makeOnClick('no')}>
            <Translate>No</Translate>
          </Button>
        </Button.Group>
        {!!price && value === 'yes' && (
          <Label pointing="left" styleName="price-tag">
            {price.toFixed(2)} {currency}
          </Label>
        )}
        {!!placesLimit && (
          <div style={{marginLeft: '1em'}}>
            <PlacesLeft placesLeft={placesLimit} isEnabled={!disabled} />
          </div>
        )}
      </div>
    </Form.Field>
  );
}

BooleanInput.propTypes = {
  disabled: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.string,
  price: PropTypes.number,
  placesLimit: PropTypes.number,
};

BooleanInput.defaultProps = {
  disabled: false,
  isRequired: false,
  defaultValue: '',
  price: 0,
  placesLimit: 0,
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
