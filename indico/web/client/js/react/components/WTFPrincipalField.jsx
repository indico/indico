// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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
  searchToken,
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
      searchToken={searchToken}
    />
  );
}

WTFPrincipalField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  defaultValue: PropTypes.string,
  withExternalUsers: PropTypes.bool,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  searchToken: PropTypes.string,
};

WTFPrincipalField.defaultProps = {
  defaultValue: [],
  withExternalUsers: false,
  required: false,
  disabled: false,
  searchToken: null,
};
