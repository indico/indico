// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import MdEditor from 'react-markdown-editor-lite';

import {formatters, FinalField} from 'indico/react/forms';
import {Markdown} from 'indico/react/util';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import './MarkdownEditor.module.scss';
import 'react-markdown-editor-lite/lib/index.css';

export default function MarkdownEditor({height, imageUploadURL, ...rest}) {
  const plugins = [
    'header',
    'font-bold',
    'font-italic',
    'list-unordered',
    'list-ordered',
    'block-quote',
    'block-code-inline',
    'block-code-block',
    'link',
    'image',
    'clear',
    'logger',
    'mode-toggle',
    'full-screen',
    'tab-insert',
  ];

  const onImageUpload = async file => {
    const bodyFormData = new FormData();
    bodyFormData.append('upload', file);
    let resp;
    try {
      resp = await indicoAxios.post(imageUploadURL, bodyFormData);
    } catch (err) {
      handleAxiosError(err);
      return;
    }
    return resp.data.url;
  };

  const handleDragOver = evt => {
    if (imageUploadURL) {
      evt.preventDefault();
    }
  };

  return (
    <div styleName="markdown-editor" onDragOver={handleDragOver}>
      <MdEditor
        renderHTML={text => <Markdown>{text.replace(/\n/gi, '  \n')}</Markdown>}
        canView={{menu: true, md: true, html: false, fullScreen: false, hideMenu: false}}
        plugins={plugins.filter(p => imageUploadURL || p !== 'image')}
        style={{height}}
        onImageUpload={imageUploadURL ? onImageUpload : undefined}
        {...rest}
      />
    </div>
  );
}

MarkdownEditor.propTypes = {
  height: PropTypes.string,
  imageUploadURL: PropTypes.string,
};

MarkdownEditor.defaultProps = {
  height: '475px',
  imageUploadURL: null,
};

export function FinalMarkdownEditor({name, ...rest}) {
  return (
    <FinalField
      name={name}
      parse={v => v.text}
      component={MarkdownEditor}
      format={formatters.trim}
      formatOnBlur
      {...rest}
    />
  );
}

FinalMarkdownEditor.propTypes = {
  name: PropTypes.string.isRequired,
};
