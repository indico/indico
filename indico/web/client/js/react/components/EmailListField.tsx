// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';

import {Translate} from 'indico/react/i18n';

import {FinalField} from '../forms';

import TagListField, {FinalTagListProps, TagListFieldComponentProps} from './TagListField';

/**
 * A field that lets the user enter email addresses
 */
const EmailListField = (props: TagListFieldComponentProps) => {
  return (
    <TagListField
      {...props}
      isValid={value => /^\S+@\S+\.\S+$/.test(value)}
      placeholder={Translate.string('Please enter an email address')}
      additionLabel={Translate.string('Add email') + ' '} // eslint-disable-line prefer-template
    />
  );
};

export default React.memo(EmailListField);

/**
 * Like `FinalField` but for a `EmailListField`.
 */
export function FinalEmailList({name, ...rest}: FinalTagListProps) {
  return <FinalField name={name} component={EmailListField} isEqual={_.isEqual} {...rest} />;
}
