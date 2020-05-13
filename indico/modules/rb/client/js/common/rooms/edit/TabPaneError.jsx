// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {useFormState} from 'react-final-form';
import {Icon} from 'semantic-ui-react';

export default function TabPaneError({fields}) {
  const {errors, submitErrors} = useFormState({errors: true, submitErrors: true});

  if (!Object.keys({...errors, ...submitErrors}).some(name => fields.includes(name))) {
    return null;
  }

  return (
    <Icon
      circular
      inverted
      name="warning"
      size="small"
      color="red"
      style={{margin: '0 0 0 10px'}}
    />
  );
}

TabPaneError.propTypes = {
  fields: PropTypes.arrayOf(PropTypes.string).isRequired,
};
