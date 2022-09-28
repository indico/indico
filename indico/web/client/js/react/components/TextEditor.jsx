// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {CKEditor} from '@ckeditor/ckeditor5-react';
import ClassicEditor from 'ckeditor';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useMemo} from 'react';
import {Field} from 'react-final-form';
import {Dimmer, Loader} from 'semantic-ui-react';

import {getConfig} from 'indico/ckeditor';
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
  const config = useMemo(() => getConfig(_config), [_config]);
  const onReady = editor => {
    editor.editing.view.change(writer => {
      writer.setStyle('width', width, editor.editing.view.document.getRoot());
      writer.setStyle('height', height, editor.editing.view.document.getRoot());
    });
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
  };

  return (
    <Dimmer.Dimmable>
      <Dimmer inverted active={loading}>
        <Loader />
      </Dimmer>
      <CKEditor
        editor={ClassicEditor}
        data={value}
        onReady={onReady}
        config={config}
        onFocus={onFocus}
        onBlur={onBlur}
        onChange={_.debounce((evt, editor) => {
          onChange(editor.getData());
        }, 250)}
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
  value: PropTypes.string.isRequired,
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
