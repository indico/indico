// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React, {useCallback, useReducer, useContext, useRef} from 'react';
import PropTypes from 'prop-types';
import {useDropzone} from 'react-dropzone';
import {Icon} from 'semantic-ui-react';
import {FileManagerContext, filePropTypes, uploadFiles} from './util';
import FileList from './FileList';
import Uploads from './Uploads';
import reducer from './reducer';
import * as actions from './actions';

import './FileManager.module.scss';

const fileTypePropTypes = {
  name: PropTypes.string.isRequired,
  files: filePropTypes.isRequired,
  contentTypes: PropTypes.arrayOf(PropTypes.string).isRequired,
  multiple: PropTypes.bool.isRequired,
  id: PropTypes.string.isRequired,
};

function Dropzone({eventId, fileType: {id, multiple, files}}) {
  const dispatch = useContext(FileManagerContext);
  const acceptsNewFiles = multiple || !files.length;

  const onDrop = useCallback(
    acceptedFiles => {
      if (!multiple) {
        acceptedFiles = acceptedFiles.splice(0, 1);
      }

      uploadFiles(
        acceptsNewFiles ? actions.markUploaded : actions.markModified,
        id,
        acceptedFiles,
        eventId,
        dispatch,
        acceptsNewFiles ? null : files[0].id
      );
    },
    [acceptsNewFiles, multiple, files, id, eventId, dispatch]
  );

  const {getRootProps, getInputProps, isDragActive} = useDropzone({onDrop});

  return (
    <div {...getRootProps()}>
      <input {...getInputProps()} />
      <div styleName="dropzone" className={isDragActive ? 'active' : ''}>
        <Icon color="grey" size="big" name={acceptsNewFiles ? 'plus circle' : 'exchange'} />
      </div>
    </div>
  );
}

Dropzone.propTypes = {
  eventId: PropTypes.string.isRequired,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
};

function FileType({eventId, fileType, uploads}) {
  const ref = useRef(null);
  return (
    <div styleName="file-type">
      <h3>{fileType.name}</h3>
      <FileList files={fileType.files} fileTypeId={fileType.id} multiple={fileType.multiple} />
      {!_.isEmpty(uploads) && <Uploads uploads={uploads} />}
      <Dropzone dropzoneRef={ref} fileType={fileType} eventId={eventId} />
    </div>
  );
}

FileType.propTypes = {
  eventId: PropTypes.string.isRequired,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
  uploads: PropTypes.objectOf(
    PropTypes.shape({
      file: PropTypes.object.isRequired,
      progress: PropTypes.number,
    })
  ),
};

FileType.defaultProps = {
  uploads: {},
};

export default function FileManager({eventId, fileTypes}) {
  const [state, dispatch] = useReducer(reducer, {fileTypes, uploads: {}});

  return (
    <div styleName="file-manager">
      <FileManagerContext.Provider value={dispatch}>
        {state.fileTypes.map(fileType => (
          <FileType
            key={fileType.id}
            eventId={eventId}
            fileType={fileType}
            uploads={state.uploads[fileType.id]}
          />
        ))}
      </FileManagerContext.Provider>
    </div>
  );
}

FileManager.propTypes = {
  eventId: PropTypes.string.isRequired,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
};
