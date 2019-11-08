// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useCallback, useReducer, useContext, useRef} from 'react';
import PropTypes from 'prop-types';
import {useDropzone} from 'react-dropzone';
import {Icon} from 'semantic-ui-react';
import {FileManagerContext, filePropTypes} from './util';
import FileList from './FileList';
import reducer from './reducer';
import styles from './FileManager.module.scss';

const fileTypePropTypes = {
  name: PropTypes.string.isRequired,
  files: filePropTypes.isRequired,
  contentTypes: PropTypes.arrayOf(PropTypes.string).isRequired,
  multiple: PropTypes.bool.isRequired,
  id: PropTypes.string.isRequired,
};

function Dropzone({fileType: {id, multiple, files}}) {
  const dispatch = useContext(FileManagerContext);
  const onDrop = useCallback(
    acceptedFiles => {
      if (!multiple && files.length) {
        dispatch({
          type: 'MODIFY',
          fileTypeId: id,
          fileId: files[0].id,
          file: {name: acceptedFiles[0].name, id: 'file2', url: 'file2url', claimed: false},
        });
      } else {
        dispatch({
          type: 'UPLOAD',
          fileTypeId: id,
          files: acceptedFiles.map(acceptedFile => ({
            name: acceptedFile.name,
            id: 'file2',
            url: 'file2url',
            claimed: false,
          })),
        });
      }
    },
    [id, multiple, files, dispatch]
  );

  const {getRootProps, getInputProps, isDragActive} = useDropzone({onDrop});

  return (
    <div {...getRootProps()}>
      <input {...getInputProps()} />
      <div className={`${styles.dropzone} ${isDragActive ? 'active' : ''}`}>
        <Icon color="grey" size="big" name={multiple ? 'plus circle' : 'exchange'} />
      </div>
    </div>
  );
}

Dropzone.propTypes = {
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
};

function FileType(fileType) {
  const ref = useRef(null);
  return (
    <div styleName="file-type">
      <h3>{fileType.name}</h3>
      <FileList files={fileType.files} fileTypeId={fileType.id} multiple={fileType.multiple} />
      <Dropzone dropzoneRef={ref} fileType={fileType} />
    </div>
  );
}

FileType.propTypes = fileTypePropTypes.isRequired;

export default function FileManager({fileTypes}) {
  const [state, dispatch] = useReducer(reducer, fileTypes);

  return (
    <div styleName="file-manager">
      <FileManagerContext.Provider value={dispatch}>
        {state.map(fileType => (
          <FileType key={fileType.id} {...fileType} />
        ))}
      </FileManagerContext.Provider>
    </div>
  );
}

FileManager.propTypes = {
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
};
