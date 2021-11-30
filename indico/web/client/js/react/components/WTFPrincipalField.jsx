// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useMemo, useState} from 'react';

import {PrincipalField} from 'indico/react/components/principals';
import {useFavoriteUsers} from 'indico/react/hooks';

import './WTFPrincipalField.module.scss';

export default function WTFPrincipalField({
  fieldId,
  defaultValue,
  required,
  disabled,
  withExternalUsers,
  eventId,
  categoryId,
}) {
  const favoriteUsersController = useFavoriteUsers();
  const inputField = useMemo(() => document.getElementById(fieldId), [fieldId]);
  const [value, setValue] = useState(defaultValue);

  const onChangePrincipal = useCallback(
    principal => {
      inputField.value = principal;
      setValue(principal);
      inputField.dispatchEvent(new Event('change', {bubbles: true}));
    },
    [inputField]
  );

  return (
    <PrincipalField
      favoriteUsersController={favoriteUsersController}
      withExternalUsers={withExternalUsers}
      required={required}
      disabled={disabled}
      onChange={onChangePrincipal}
      onFocus={() => {}}
      onBlur={() => {}}
      value={value}
      styleName="fixed-width"
      eventId={eventId}
      categoryId={categoryId}
    />
  );
}

WTFPrincipalField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  defaultValue: PropTypes.string,
  withExternalUsers: PropTypes.bool,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  eventId: PropTypes.number,
  categoryId: PropTypes.number,
};

WTFPrincipalField.defaultProps = {
  defaultValue: [],
  withExternalUsers: false,
  required: false,
  disabled: false,
  eventId: null,
  categoryId: null,
};
