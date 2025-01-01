// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Rating} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';

import './ReviewRating.module.scss';

export default function ReviewRating({min, max, value, disabled, onChange}) {
  const ratingRange = _.range(min, max + 1);
  const suiRatingRange = _.range(1, ratingRange.length + 1);
  const maxRating = suiRatingRange[suiRatingRange.length - 1];
  const rating = suiRatingRange[ratingRange.findIndex(item => item === value)];

  return (
    <span styleName="rating-field">
      <Rating
        maxRating={maxRating}
        rating={value === null ? null : rating}
        disabled={disabled}
        onRate={(evt, {rating: newRating}) => {
          // map the value from SUIR Rating to the corresponding value between min and max
          const val = ratingRange[suiRatingRange.findIndex(item => item === newRating)];
          onChange(val);
        }}
        clearable
      />
      <span styleName="rating-value">{value !== null ? value : '-'}</span>
    </span>
  );
}

ReviewRating.propTypes = {
  min: PropTypes.number,
  max: PropTypes.number.isRequired,
  value: PropTypes.number,
  disabled: PropTypes.bool,
  onChange: PropTypes.func,
};

ReviewRating.defaultProps = {
  min: 0,
  value: null,
  disabled: false,
  onChange: null,
};

export function FinalRating({name, label, ...rest}) {
  return (
    <FinalField
      {...rest}
      name={name}
      label={label}
      component={ReviewRating}
      undefinedValue={null}
      format={v => v}
    />
  );
}

FinalRating.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string,
};

FinalRating.defaultProps = {
  label: null,
};
