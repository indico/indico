// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadFileURL from 'indico-url:event_editing.file_upload';
import React, {useCallback, useReducer, useContext, useRef} from 'react';
import PropTypes from 'prop-types';
import {useDropzone} from 'react-dropzone';
import {Icon} from 'semantic-ui-react';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
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

const uploadFile = async (type, fileTypeId, acceptedFile, eventId, dispatch, fileId = null) => {
  const headers = {'content-type': 'multipart/form-data'};
  const formData = new FormData();
  let response;
  formData.append('file', acceptedFile);
  try {
    response = await indicoAxios.post(uploadFileURL({confId: eventId}), formData, {headers});
  } catch (e) {
    handleAxiosError(e, false, true);
    return;
  }
  const file = response.data;
  dispatch({
    type,
    fileTypeId,
    fileId,
    file: {name: file.filename, id: file.uuid, url: 'url2file', claimed: false},
  });
};

function Dropzone({eventId, fileType: {id, multiple, files}}) {
  const dispatch = useContext(FileManagerContext);
  const onDrop = useCallback(
    acceptedFiles => {
      if (!multiple && files.length) {
        uploadFile('MODIFY', id, acceptedFiles[0], eventId, dispatch, files[0].id);
      } else {
        acceptedFiles.forEach(acceptedFile =>
          uploadFile('UPLOAD', id, acceptedFile, eventId, dispatch)
        );
      }
    },
    [id, eventId, multiple, files, dispatch]
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
  eventId: PropTypes.string.isRequired,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
};

function FileType({eventId, fileType}) {
  const ref = useRef(null);
  return (
    <div styleName="file-type">
      <h3>{fileType.name}</h3>
      <FileList files={fileType.files} fileTypeId={fileType.id} multiple={fileType.multiple} />
      <Dropzone dropzoneRef={ref} fileType={fileType} eventId={eventId} />
    </div>
  );
}

FileType.propTypes = {
  eventId: PropTypes.string.isRequired,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
};

export default function FileManager({eventId, fileTypes}) {
  const [state, dispatch] = useReducer(reducer, fileTypes);

  return (
    <div styleName="file-manager">
      <FileManagerContext.Provider value={dispatch}>
        {state.map(fileType => (
          <FileType key={fileType.id} eventId={eventId} fileType={fileType} />
        ))}
      </FileManagerContext.Provider>
    </div>
  );
}

FileManager.propTypes = {
  eventId: PropTypes.string.isRequired,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
};
