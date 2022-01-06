// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import {Checkbox, Form, Label} from 'semantic-ui-react';

import {getCurrency} from '../../form_setup/selectors';

import '../../../styles/regform.module.scss';

export default function CheckboxInput({htmlName, disabled, title, isRequired, price}) {
  const currency = useSelector(getCurrency);
  const [checked, setChecked] = useState(false);

  return (
    <Form.Field required={isRequired} disabled={disabled} styleName="field">
      <Checkbox
        name={htmlName}
        label={title}
        checked={checked}
        onClick={() => setChecked(!checked)}
      />
      {!!price && (
        <Label pointing="left" styleName={`price-tag ${!checked ? 'greyed' : ''}`}>
          {price.toFixed(2)} {currency}
        </Label>
      )}
    </Form.Field>
  );
}

CheckboxInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
  price: PropTypes.number,
};

CheckboxInput.defaultProps = {
  disabled: false,
  price: 0,
};
