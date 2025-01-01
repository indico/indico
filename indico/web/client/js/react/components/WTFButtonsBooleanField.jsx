// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';

import {Translate} from '../i18n';

import IButton from './IButton';

export default function WTFButtonsBooleanField({checkboxId, trueCaption, falseCaption, disabled}) {
  const checkboxField = useMemo(() => document.getElementById(checkboxId), [checkboxId]);
  const [value, setValue] = useState(JSON.parse(checkboxField.value));
  const [trueText, trueIcon] = trueCaption;
  const [falseText, falseIcon] = falseCaption;

  const handleSetTrue = () => {
    setValue(true);
    checkboxField.value = true;
    checkboxField.dispatchEvent(new Event('change', {bubbles: true}));
  };

  const handleSetFalse = () => {
    setValue(false);
    checkboxField.value = false;
    checkboxField.dispatchEvent(new Event('change', {bubbles: true}));
  };

  return (
    <>
      <IButton icon={trueIcon} highlight={value} onClick={handleSetTrue} disabled={disabled}>
        <strong>{trueText}</strong>
      </IButton>

      <IButton icon={falseIcon} highlight={!value} onClick={handleSetFalse} disabled={disabled}>
        <strong>{falseText}</strong>
      </IButton>
    </>
  );
}

WTFButtonsBooleanField.propTypes = {
  checkboxId: PropTypes.string.isRequired,
  trueCaption: PropTypes.node,
  falseCaption: PropTypes.node,
  disabled: PropTypes.bool,
};

WTFButtonsBooleanField.defaultProps = {
  trueCaption: [Translate.string('Yes')],
  falseCaption: [Translate.string('No')],
  disabled: false,
};
