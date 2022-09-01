// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {CKEditor} from '@ckeditor/ckeditor5-react';
import ClassicEditor from 'ckeditor';
import PropTypes from 'prop-types';
import React, {useMemo} from 'react';
import {Dimmer, Loader} from 'semantic-ui-react';

import {getConfig} from 'indico/ckeditor';

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
  ...rest
}) {
  const config = useMemo(() => getConfig(_config), [_config]);
  const onReady = editor => {
    editor.editing.view.change(writer => {
      writer.setStyle('width', width, editor.editing.view.document.getRoot());
      writer.setStyle('height', height, editor.editing.view.document.getRoot());
    });
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
        onChange={(evt, editor) => {
          onChange(editor.getData());
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
  value: PropTypes.string.isRequired,
  config: PropTypes.object,
  loading: PropTypes.bool,
};

TextEditor.defaultProps = {
  height: '400px',
  width: undefined,
  onReady: undefined,
  config: undefined,
  loading: false,
};

export function FinalTextEditor({name, ...rest}) {
  return <FinalField name={name} component={TextEditor} {...rest} />;
}

FinalTextEditor.propTypes = {
  name: PropTypes.string.isRequired,
};
