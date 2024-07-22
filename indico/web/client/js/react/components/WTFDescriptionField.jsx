// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState, useEffect} from 'react';
import {Form} from 'semantic-ui-react';

import {MarkdownEditor, TinyMCETextEditor} from 'indico/react/components';

export default function WTFDescriptionField({
  fieldId,
  required,
  disabled,
  renderMode,
  imageUploadURL,
  height,
  currentInput,
}) {
  const [inputValue, setInputValue] = useState(currentInput);

  useEffect(() => {
    setInputValue(currentInput);
  }, [currentInput]);

  const handleHTMLChange = newValue => {
    setInputValue(newValue);
    const descriptionField = $(`#${fieldId}`);
    // Update the hidden input field directly using jQuery
    descriptionField.val(newValue);
    descriptionField.trigger('change');
  };

  const handleMarkdownChange = newValue => {
    setInputValue(newValue['text']);
    const descriptionField = $(`#${fieldId}`);
    // Update the hidden input field directly using jQuery
    descriptionField.val(newValue['text']);
    descriptionField.trigger('change');
  };

  return (
    <Form.Field>
      {renderMode === 'markdown' && (
        <MarkdownEditor
          name={fieldId}
          fieldId={fieldId}
          imageUploadURL={imageUploadURL}
          height={height}
          required={required}
          disabled={disabled}
          value={inputValue}
          onChange={handleMarkdownChange}
        />
      )}
      {renderMode === 'html' && (
        <TinyMCETextEditor
          name={fieldId}
          fieldId={fieldId}
          value={inputValue}
          parse={v => v}
          config={{images: true, imageUploadURL, fullScreen: false}}
          height={height}
          required={required}
          disabled={disabled}
          onBlur={v => v}
          onChange={handleHTMLChange}
          onFocus={v => v}
        />
      )}
    </Form.Field>
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
