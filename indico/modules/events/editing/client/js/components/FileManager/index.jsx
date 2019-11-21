// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React, {useCallback, useReducer, useContext, useRef, useMemo} from 'react';
import PropTypes from 'prop-types';
import {useDropzone} from 'react-dropzone';
import {Button, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {deleteFile, FileManagerContext, filePropTypes, mapFileTypes, uploadFiles} from './util';
import FileList from './FileList';
import Uploads from './Uploads';
import reducer from './reducer';
import * as actions from './actions';

import './FileManager.module.scss';

const fileTypePropTypes = {
  name: PropTypes.string.isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)),
  extensions: PropTypes.arrayOf(PropTypes.string).isRequired,
  allowMultipleFiles: PropTypes.bool.isRequired,
  id: PropTypes.number.isRequired,
};

function Dropzone({uploadURL, fileType: {id, allowMultipleFiles, files}}) {
  const dispatch = useContext(FileManagerContext);
  const acceptsNewFiles = allowMultipleFiles || !files.length;

  const onDrop = useCallback(
    async acceptedFiles => {
      if (!allowMultipleFiles) {
        acceptedFiles = acceptedFiles.splice(0, 1);
      }
      await uploadFiles(
        acceptsNewFiles ? actions.markUploaded : actions.markModified,
        id,
        acceptedFiles,
        uploadURL,
        dispatch,
        acceptsNewFiles ? null : files[0].uuid
      );
      if (files.length && files[0].state === 'modified') {
        // we're modifying a "modified" file, so we can get rid of
        // the current one
        dispatch(deleteFile(files[0].uuid));
      }
    },
    [acceptsNewFiles, allowMultipleFiles, files, id, uploadURL, dispatch]
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
  uploadURL: PropTypes.string.isRequired,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
};

function FileType({uploadURL, fileType, uploads}) {
  const ref = useRef(null);
  return (
    <div styleName="file-type">
      <h3>{fileType.name}</h3>
      <FileList
        files={fileType.files}
        fileTypeId={fileType.id}
        allowMultipleFiles={fileType.allowMultipleFiles}
        uploadURL={uploadURL}
      />
      {!_.isEmpty(uploads) && <Uploads uploads={uploads} />}
      <Dropzone dropzoneRef={ref} fileType={fileType} uploadURL={uploadURL} />
    </div>
  );
}

FileType.propTypes = {
  uploadURL: PropTypes.string.isRequired,
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

export default function FileManager({downloadURL, uploadURL, fileTypes, files}) {
  const _fileTypes = useMemo(() => mapFileTypes(fileTypes, files), [fileTypes, files]);
  const [state, dispatch] = useReducer(reducer, {
    fileTypes: _fileTypes,
    uploads: {},
  });

  return (
    <div styleName="file-manager-wrapper">
      <div styleName="file-manager">
        <FileManagerContext.Provider value={dispatch}>
          {state.fileTypes.map(fileType => (
            <FileType
              key={fileType.id}
              uploadURL={uploadURL}
              fileType={fileType}
              uploads={state.uploads[fileType.id]}
            />
          ))}
        </FileManagerContext.Provider>
      </div>
      {downloadURL && files.length !== 0 && (
        <div>
          <Button as="a" href={downloadURL} floated="right" icon primary>
            <Icon name="download" /> <Translate>Download ZIP</Translate>
          </Button>
        </div>
      )}
    </div>
  );
}

FileManager.propTypes = {
  downloadURL: PropTypes.string.isRequired,
  uploadURL: PropTypes.string.isRequired,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
};
