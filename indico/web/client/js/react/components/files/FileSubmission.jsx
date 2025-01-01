// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useState} from 'react';
import {useDropzone} from 'react-dropzone';

import {FileArea} from './FileArea';

export default function FileSubmission({onChange, disabled}) {
  const [files, setFiles] = useState([]);

  const onDrop = useCallback(
    acceptedFiles => {
      const newFilenames = new Set(acceptedFiles.map(f => f.name));
      acceptedFiles = files.filter(f => !newFilenames.has(f.name)).concat(acceptedFiles);
      setFiles(acceptedFiles);
      if (onChange) {
        onChange(acceptedFiles);
      }
    },
    [files, setFiles, onChange]
  );

  const dropzone = useDropzone({
    onDrop,
    disabled,
    multiple: true,
    noClick: true,
    noKeyboard: true,
  });

  const removeFile = file => {
    const newFiles = files.filter(f => f.name !== file.filename);
    setFiles(newFiles);
    if (onChange) {
      onChange(newFiles);
    }
  };

  return (
    <FileArea
      dropzone={dropzone}
      files={files.map(({name, size}) => ({filename: name, size}))}
      fileAction={{
        icon: 'trash',
        color: 'red',
        onClick: removeFile,
      }}
    />
  );
}

FileSubmission.propTypes = {
  onChange: PropTypes.func,
  disabled: PropTypes.bool,
};

FileSubmission.defaultProps = {
  onChange: null,
  disabled: false,
};
