// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {fileTypePropTypes, filePropTypes, mapFileTypes} from '../FileManager/util';
import './FileDisplay.module.scss';

function FileListDisplay({files}) {
  return (
    <ul styleName="file-list-display">
      {files.map(({filename, uuid}) => (
        <li key={uuid}>
          <span styleName="file-name">
            <a>{filename}</a>
          </span>
        </li>
      ))}
    </ul>
  );
}

FileListDisplay.propTypes = {
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
};

function FileTypeDisplay({fileType}) {
  return (
    <div styleName="file-type-display">
      <h3>{fileType.name}</h3>
      <FileListDisplay files={fileType.files} />
    </div>
  );
}

FileTypeDisplay.propTypes = {
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
};

export default function FileDisplay({fileTypes, files}) {
  return (
    <div styleName="file-display">
      {mapFileTypes(fileTypes, files).map(fileType => (
        <FileTypeDisplay key={fileType.id} fileType={fileType} />
      ))}
    </div>
  );
}

FileDisplay.propTypes = {
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
};
