// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'tinymce/tinymce';

import {Editor} from '@tinymce/tinymce-react';
import PropTypes from 'prop-types';
import React, {useMemo} from 'react';
import {Dimmer, Loader} from 'semantic-ui-react';

import {getConfig} from 'indico/tinymce';

import {FinalField} from '../forms';

export default function TinyMCETextEditor({
  value,
  initialValue,
  height,
  config: _config,
  loading,
  disabled,
  onChange,
  onFocus,
  onBlur,
  lazyValue,
}) {
  const contentCSS = useMemo(() => JSON.parse(document.body.dataset.tinymceContentCss), []);
  if (lazyValue && typeof value === 'string') {
    value = {initialValue: value, getData: () => value};
  }

  const config = useMemo(
    () =>
      getConfig(
        undefined,
        {height, contentCSS, ..._config},
        {
          onChange: editor => {
            if (lazyValue) {
              onChange({...value, getData: () => editor.getContent()});
            } else {
              onChange(editor.getContent());
            }
          },
        }
      ),
    [_config, height, onChange, contentCSS, lazyValue, value]
  );

  return (
    <Dimmer.Dimmable>
      <Dimmer inverted active={loading}>
        <Loader />
      </Dimmer>
      <Editor
        init={config}
        value={lazyValue ? undefined : value}
        initialValue={lazyValue ? value.initialValue : initialValue}
        onFocus={onFocus}
        onBlur={onBlur}
        // disable the editor if it's set to show the loading animation, since otherwise you could
        // still tab into it and change its contents
        disabled={disabled || loading}
        // XXX if you touch this make sure it remains longer than maxWait in the tinymce config
        rollback={1250}
      />
    </Dimmer.Dimmable>
  );
}

TinyMCETextEditor.propTypes = {
  height: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({initialValue: PropTypes.string, getData: PropTypes.func}),
  ]),
  initialValue: PropTypes.string,
  config: PropTypes.object,
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
  lazyValue: PropTypes.bool,
};

TinyMCETextEditor.defaultProps = {
  height: 525,
  config: undefined,
  loading: false,
  disabled: false,
  value: undefined,
  initialValue: undefined,
  lazyValue: false,
};

export function FinalTinyMCETextEditor({name, ...rest}) {
  return <FinalField name={name} component={TinyMCETextEditor} {...rest} />;
}

FinalTinyMCETextEditor.propTypes = {
  name: PropTypes.string.isRequired,
};
