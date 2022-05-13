import {CKEditor} from '@ckeditor/ckeditor5-react';
import ClassicEditor from 'ckeditor';
import PropTypes from 'prop-types';
import React from 'react';

import {getConfig, onReady} from 'indico/ckeditor';

export default function TextEditor({width, height, ...rest}) {
  return (
    <CKEditor editor={ClassicEditor} onReady={onReady} configuration={{...getConfig(), ...rest}} />
  );
}

TextEditor.propTypes = {
  width: PropTypes.number,
  height: PropTypes.number,
};

TextEditor.defaultProps = {
  height: 400,
  width: undefined,
};
