// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import WTFDescriptionField from "indico/react/components/WTFDescriptionField";

(function (global) {
  global.setupNewMarkDownEditor = function setupNewMarkDownEditor({
  fieldId,
  required,
  disabled,
  renderMode,
  imageUploadURL,
  height
  }) {
  const field = document.getElementById(fieldId);
  const currentInput = field.value
  ReactDOM.render(
    <WTFDescriptionField fieldId={fieldId} required={required} disabled={disabled} renderMode={renderMode}
                         imageUploadURL={imageUploadURL} height={height} currentInput={currentInput}/>,
    document.getElementById(fieldId)
  );
};
})(window);
