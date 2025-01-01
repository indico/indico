// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useEffect, useMemo, useState} from 'react';

import {PrincipalListField} from 'indico/react/components/principals';
import {FormContext} from 'indico/react/forms';
import {useFavoriteUsers} from 'indico/react/hooks';

import './WTFPrincipalListField.module.scss';

export default function WTFPrincipalListField({
  formContext,
  fieldId,
  defaultValue,
  protectedFieldId,
  ...otherProps
}) {
  const favoriteUsersController = useFavoriteUsers();
  const protectedField = useMemo(
    () => protectedFieldId && document.getElementById(protectedFieldId),
    [protectedFieldId]
  );
  const inputField = useMemo(() => document.getElementById(fieldId), [fieldId]);
  const [value, setValue] = useState(defaultValue);
  const [disabled, setDisabled] = useState(!!protectedField && !protectedField.checked);

  useEffect(() => {
    if (!protectedField) {
      return;
    }
    const onChangeProtected = () => {
      setDisabled(!protectedField.checked);
    };
    protectedField.addEventListener('change', onChangeProtected);
    return () => protectedField.removeEventListener('change', onChangeProtected);
  }, [protectedField]);

  const onChangePrincipal = useCallback(
    principals => {
      inputField.value = JSON.stringify(principals);
      setValue(principals);
      inputField.dispatchEvent(new Event('change', {bubbles: true}));
    },
    [inputField]
  );

  return (
    <FormContext.Provider value={formContext}>
      <PrincipalListField
        favoriteUsersController={favoriteUsersController}
        disabled={disabled}
        onChange={onChangePrincipal}
        onFocus={() => {}}
        onBlur={() => {}}
        value={value}
        styleName="opaque"
        {...otherProps}
      />
    </FormContext.Provider>
  );
}

WTFPrincipalListField.propTypes = {
  formContext: PropTypes.arrayOf(PropTypes.string).isRequired,
  fieldId: PropTypes.string.isRequired,
  defaultValue: PropTypes.arrayOf(PropTypes.string),
  protectedFieldId: PropTypes.string,
};

WTFPrincipalListField.defaultProps = {
  defaultValue: [],
  protectedFieldId: null,
};
