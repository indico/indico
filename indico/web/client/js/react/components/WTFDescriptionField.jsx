// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef, useState} from 'react';
import {Form} from 'semantic-ui-react';

import {ConfirmButton, MarkdownEditor, TinyMCETextEditor} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

export default function WTFDescriptionField({
  fieldId,
  required,
  disabled,
  currentRenderMode,
  imageUploadURL,
  height,
  currentInput,
}) {
  const [inputValue, setInputValue] = useState(currentInput);
  const [renderMode, setRenderMode] = useState(currentRenderMode);
  const markdownEditorRef = useRef(null);

  const updateHiddenField = value => {
    const descriptionField = document.getElementById(fieldId);
    if (descriptionField) {
      descriptionField.value = value;
      descriptionField.dispatchEvent(new Event('change', {bubbles: true}));
    }
  };

  const updateRenderMode = newRenderMode => {
    const renderModeField = document.getElementById('render_mode');
    renderModeField.value = newRenderMode === 'html' ? '1' : '2';
    renderModeField.dispatchEvent(new Event('change', {bubbles: true}));
  };

  const handleHTMLChange = newValue => {
    setInputValue(newValue);
    updateHiddenField(newValue);
  };

  const handleMarkdownChange = newValue => {
    setInputValue(newValue);
    updateRenderMode('markdown');
    updateHiddenField(newValue.text);
  };

  const convertToHTML = () => {
    setRenderMode('html');
    updateRenderMode('html');
    updateHiddenField(inputValue.html || inputValue);
  };

  return (
    <Form.Field>
      {renderMode === 'markdown' && (
        <>
          <MarkdownEditor
            key="markdown-editor"
            ref={markdownEditorRef}
            name={fieldId}
            fieldId={fieldId}
            imageUploadURL={imageUploadURL}
            height={height}
            required={required}
            disabled={disabled}
            value={typeof inputValue === 'object' ? inputValue.text || '' : inputValue || ''}
            onChange={handleMarkdownChange}
          />
          <div className="convert-button-container" style={{marginTop: '1rem'}}>
            <ConfirmButton
              type="button"
              onClick={convertToHTML}
              basic
              disabled={!inputValue.html}
              popupContent={Translate.string(
                'You cannot switch back to Markdown after switching to HTML.'
              )}
            >
              <Translate>Use rich-text (HTML) editor</Translate>
            </ConfirmButton>
          </div>
        </>
      )}
      {renderMode === 'html' && (
        <TinyMCETextEditor
          key="html-editor"
          name={fieldId}
          fieldId={fieldId}
          value={typeof inputValue === 'object' ? inputValue.html || '' : inputValue || ''}
          parse={v => v}
          config={{images: true, imageUploadURL, fullScreen: false}}
          height={height}
          required={required}
          disabled={disabled}
          onChange={handleHTMLChange}
          onBlur={v => v}
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
  currentRenderMode: PropTypes.string.isRequired,
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
