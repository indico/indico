// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {CKEditor} from '@ckeditor/ckeditor5-react';
import ClassicEditor from 'ckeditor';
import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {Field} from 'react-final-form';
import {Dimmer, Loader} from 'semantic-ui-react';

import {getConfig, sanitizeHtml} from 'indico/ckeditor';
import {Translate} from 'indico/react/i18n';

import {FinalField} from '../forms';

export default function TextEditor({
  value,
  width,
  height,
  onReady: _onReady,
  config: _config,
  loading,
  onChange,
  onFocus,
  onBlur,
  setValidationError,
  ...rest
}) {
  if (typeof value === 'string') {
    value = {initialValue: value, getData: () => value};
  }

  const [ready, setReady] = useState(false);
  const config = useMemo(() => getConfig(_config), [_config]);
  const onReady = editor => {
    editor.editing.view.change(writer => {
      writer.setStyle('width', width, editor.editing.view.document.getRoot());
      writer.setStyle('height', height, editor.editing.view.document.getRoot());
    });
    // Sanitize pasted HTML
    // https://ckeditor.com/docs/ckeditor5/latest/framework/guides/deep-dive/clipboard.html
    editor.editing.view.document.on(
      'clipboardInput',
      (ev, data) => {
        if (data.method !== 'paste' || data.content) {
          return;
        }
        const dataTransfer = data.dataTransfer;
        const contentData = dataTransfer.getData('text/html');
        if (contentData) {
          data.content = editor.data.htmlProcessor.toView(sanitizeHtml(contentData));
        }
      },
      {priority: 'normal'}
    );
    if (setValidationError) {
      editor.plugins._plugins.get('SourceEditing').on('change:isSourceEditingMode', evt => {
        if (evt.source.isSourceEditingMode) {
          setValidationError(Translate.string('Please exit source editing mode'));
        } else {
          setValidationError(undefined);
        }
      });
    }
    if (_onReady) {
      _onReady(editor);
    }
    setReady(true);
  };

  return (
    <Dimmer.Dimmable>
      <Dimmer inverted active={loading}>
        <Loader />
      </Dimmer>
      <CKEditor
        editor={ClassicEditor}
        data={value.initialValue}
        onReady={onReady}
        config={config}
        onFocus={onFocus}
        onBlur={onBlur}
        onChange={(evt, editor) => {
          // Prevent onChange firing when changing the initial data
          // https://github.com/ckeditor/ckeditor5-react/issues/270
          if (!ready) {
            return;
          }
          // Return a lazy object with a getter for the editor data.
          // Calling getData() explicitly on every change is too time consuming for
          // long texts and lags the editor as you type.
          onChange({...value, getData: () => editor.getData()});
        }}
        {...rest}
      />
    </Dimmer.Dimmable>
  );
}

TextEditor.propTypes = {
  width: PropTypes.string,
  height: PropTypes.string,
  onReady: PropTypes.func,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({initialValue: PropTypes.string, getData: PropTypes.func}),
  ]).isRequired,
  config: PropTypes.object,
  loading: PropTypes.bool,
  setValidationError: PropTypes.func,
};

TextEditor.defaultProps = {
  height: '400px',
  width: undefined,
  onReady: undefined,
  config: undefined,
  loading: false,
  setValidationError: null,
};

export function FinalTextEditor({name, ...rest}) {
  return (
    <Field
      name={`_${name}_invalidator`}
      validate={value => value || undefined}
      render={({input: {onChange: setDummyValue}}) => (
        <FinalField
          name={name}
          component={TextEditor}
          setValidationError={setDummyValue}
          {...rest}
        />
      )}
    />
  );
}

FinalTextEditor.propTypes = {
  name: PropTypes.string.isRequired,
};
