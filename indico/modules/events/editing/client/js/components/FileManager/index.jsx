// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React, {useCallback, useReducer, useContext, useRef, useMemo, useEffect} from 'react';
import PropTypes from 'prop-types';
import {useDropzone} from 'react-dropzone';
import {Icon} from 'semantic-ui-react';
import {TooltipIfTruncated} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {
  FileManagerContext,
  filePropTypes,
  fileTypePropTypes,
  uploadFiles,
  deleteFile,
  mapFileTypes,
} from './util';
import FileList from './FileList';
import Uploads from './Uploads';
import reducer from './reducer';
import * as actions from './actions';
import {getFiles} from './selectors';

import './FileManager.module.scss';

export function Dropzone({uploadURL, fileType: {id, allowMultipleFiles, files, extensions}}) {
  const dispatch = useContext(FileManagerContext);
  // we only want to modify the existing file if we do not allow multiple files and
  // there is exactly one file that is not in the 'added' state (which would imply
  // a freshly uploaded file which can be simply replaced)
  const fileToReplace =
    !allowMultipleFiles && files.length && files[0].state !== 'added' ? files[0] : null;
  // if we don't allow multiple files and have a file in the added or modified state,
  // that file can always be deleted from the server after the upload
  const fileToDelete =
    !allowMultipleFiles && files.length && ['added', 'modified'].includes(files[0].state)
      ? files[0]
      : null;
  // as far as the user is concerned, they upload a "new" file when there are no files or
  // multiple files are supported for the file type
  const showNewFileIcon = files.length === 0 || allowMultipleFiles;

  const onDropAccepted = useCallback(
    async acceptedFiles => {
      if (!allowMultipleFiles) {
        acceptedFiles = acceptedFiles.splice(0, 1);
      }
      const rv = await uploadFiles(
        fileToReplace ? actions.markModified : actions.markUploaded,
        id,
        acceptedFiles,
        uploadURL,
        dispatch,
        fileToReplace ? fileToReplace.uuid : null
      );
      // only delete if there is a file to delete and the upload of a new file didn't fail
      if (fileToDelete && rv[0] !== null) {
        // we're modifying a freshly uploaded file, so we can get rid of the current one
        deleteFile(fileToDelete.uuid);
      }
    },
    [fileToReplace, fileToDelete, allowMultipleFiles, id, uploadURL, dispatch]
  );

  const {getRootProps, getInputProps, isDragActive} = useDropzone({
    onDropAccepted,
    multiple: allowMultipleFiles,
    accept: extensions.map(ext => `.${ext}`).join(','),
  });

  return (
    <div {...getRootProps()}>
      <input {...getInputProps()} />
      <div styleName="dropzone" className={isDragActive ? 'active' : ''}>
        <Icon color="grey" size="big" name={showNewFileIcon ? 'plus circle' : 'exchange'} />
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
      <TooltipIfTruncated tooltip={fileType.extensions.join(', ')}>
        <ul styleName="file-extensions">
          {fileType.extensions.length !== 0
            ? fileType.extensions.map(ext => <li key={ext}>{ext}</li>)
            : Translate.string('(no extension restrictions)')}
        </ul>
      </TooltipIfTruncated>
      <FileList files={fileType.files} fileType={fileType} uploadURL={uploadURL} />
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

export default function FileManager({onChange, uploadURL, fileTypes, files}) {
  const _fileTypes = useMemo(() => mapFileTypes(fileTypes, files), [fileTypes, files]);
  const [state, dispatch] = useReducer(reducer, {
    fileTypes: _fileTypes,
    uploads: {},
    isDirty: false,
  });

  useEffect(() => {
    if (state.isDirty) {
      onChange(getFiles(state));
      dispatch(actions.clearDirty());
    }
  }, [onChange, state]);

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
    </div>
  );
}

FileManager.propTypes = {
  uploadURL: PropTypes.string.isRequired,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)),
  onChange: PropTypes.func.isRequired,
};

FileManager.defaultProps = {
  files: [],
};
