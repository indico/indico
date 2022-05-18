import {CKEditor} from '@ckeditor/ckeditor5-react';
import ClassicEditor from 'ckeditor';
import PropTypes from 'prop-types';
import React from 'react';

import {getConfig} from 'indico/ckeditor';

export default function TextEditor({width, height, ...rest}) {
  const onReady = editor => {
    editor.editing.view.change(writer => {
      writer.setStyle('width', width, editor.editing.view.document.getRoot());
      writer.setStyle('height', height, editor.editing.view.document.getRoot());
    });
  };

  return (
    <CKEditor editor={ClassicEditor} onReady={onReady} configuration={{...getConfig(), ...rest}} />
  );
}

TextEditor.propTypes = {
  width: PropTypes.number,
  height: PropTypes.number,
};

TextEditor.defaultProps = {
  height: '400px',
  width: undefined,
};
