// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import {getCurrency} from '../../form_setup/selectors';

import '../../../styles/regform.module.scss';

export default function CheckboxInput({htmlName, disabled, title, isRequired, price}) {
  const currency = useSelector(getCurrency);

  return (
    <>
      <label styleName="checkbox-input-label">
        <input type="checkbox" name={htmlName} disabled={disabled} />
        {title}
        {isRequired && <span styleName="required">*</span>}
      </label>
      {!!price && (
        <span styleName="price">
          {price} {currency}
        </span>
      )}
    </>
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
