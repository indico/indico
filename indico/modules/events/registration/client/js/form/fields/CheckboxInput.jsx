// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Label} from 'semantic-ui-react';

import {FinalCheckbox, FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getPriceFormatter} from '../../form/selectors';
import {getFieldValue} from '../../form_submission/selectors';

import {PlacesLeft} from './PlacesLeftLabel';

import styles from '../../../styles/regform.module.scss';

export default function CheckboxInput({
  fieldId,
  htmlId,
  htmlName,
  disabled,
  title,
  isRequired,
  showAsRequired,
  price,
  placesLimit,
  placesUsed,
  retentionPeriodIcon,
}) {
  const formatPrice = useSelector(getPriceFormatter);
  const existingValue = useSelector(state => getFieldValue(state, fieldId));

  return (
    <FinalCheckbox
      id={htmlId}
      fieldProps={{className: `${styles.field} ${showAsRequired ? 'required' : ''}`}}
      name={htmlName}
      label={title}
      disabled={disabled || (placesLimit > 0 && placesUsed >= placesLimit && !existingValue)}
      required={isRequired}
    >
      {retentionPeriodIcon}
      {!!price && (
        <Field name={htmlName} subscription={{value: true}}>
          {({input: {value: checked}}) => (
            <Label pointing="left" styleName={`price-tag ${!checked ? 'greyed' : ''}`}>
              {formatPrice(price)}
            </Label>
          )}
        </Field>
      )}
      {!!placesLimit && (
        <div style={{marginLeft: '1em', display: 'inline-block'}}>
          <PlacesLeft placesLimit={placesLimit} placesUsed={placesUsed} isEnabled={!disabled} />
        </div>
      )}
    </FinalCheckbox>
  );
}

CheckboxInput.propTypes = {
  fieldId: PropTypes.number.isRequired,
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
  showAsRequired: PropTypes.bool.isRequired,
  price: PropTypes.number,
  placesLimit: PropTypes.number.isRequired,
  placesUsed: PropTypes.number.isRequired,
  retentionPeriodIcon: PropTypes.element,
};

CheckboxInput.defaultProps = {
  disabled: false,
  price: 0,
  retentionPeriodIcon: null,
};

export function CheckboxSettings() {
  return (
    <FinalInput
      name="placesLimit"
      type="number"
      label={Translate.string('Places limit')}
      placeholder={Translate.string('None', 'Places limit')}
      step="1"
      min="1"
      validate={v.optional(v.min(0))}
      parse={val => (val === '' ? 0 : +val)}
      format={val => (val === 0 ? '' : val)}
    />
  );
}
