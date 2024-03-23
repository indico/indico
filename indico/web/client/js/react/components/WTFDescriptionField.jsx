// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';

import {FinalMarkdownEditor, FinalTinyMCETextEditor} from 'indico/react/components';

export default function WTFDescriptionField({
  fieldId,
  required,
  disabled,
  renderMode,
  imageUploadURL,
  height,
  currentInput,
}) {
  // const field = useMemo(() => document.getElementById(`${fieldId}`), [fieldId]);
  const [loading, setLoading] = useState(false);

  return (
    <>
      {renderMode === 'markdown' && (
        <FinalMarkdownEditor
          name={fieldId}
          imageUploadURL={imageUploadURL}
          height={height}
          required={required}
          disabled={disabled}
        />
      )}
      {renderMode === 'html' && (
        <FinalTinyMCETextEditor
          name={fieldId}
          loading={loading}
          value={currentInput}
          parse={v => v}
          config={{images: true, imageUploadURL, fullScreen: false}}
          height={height}
          required={required}
          disabled={disabled}
        />
      )}
    </>
  );
}

WTFDescriptionField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  renderMode: PropTypes.string.isRequired,
  imageUploadURL: PropTypes.string,
  height: PropTypes.string,
  currentInput: PropTypes.string,
};

WTFDescriptionField.defaultProps = {
  required: false,
  disabled: false,
  imageUploadURL: null,
  height: '50vh',
  currentInput: '',
};
