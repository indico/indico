// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

import {FinalField} from '../forms';

import TagListField from './TagListField';

/**
 * A field that lets the user enter email addresses
 */
const EmailListField = props => {
  return (
    <TagListField
      {...props}
      isValid={value => /^\S+@\S+\.\S+$/.test(value)}
      placeholder={Translate.string('Please enter an email address')}
      additionLabel={Translate.string('Add email') + ' '} // eslint-disable-line prefer-template
    />
  );
};

EmailListField.propTypes = {
  ...TagListField.propTypes,
};

export default React.memo(EmailListField);

/**
 * Like `FinalField` but for a `EmailListField`.
 */
export function FinalEmailList({name, ...rest}) {
  return <FinalField name={name} component={EmailListField} isEqual={_.isEqual} {...rest} />;
}

FinalEmailList.propTypes = {
  name: PropTypes.string.isRequired,
};
