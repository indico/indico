// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import deleteFileURL from 'indico-url:files.delete_file';

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';
import * as actions from './actions';
import {getFiles} from './selectors';

export const FileManagerContext = React.createContext(null);

// TODO: refactor this props to be re-used as a generic file
export const filePropTypes = {
  filename: PropTypes.string.isRequired,
  downloadURL: PropTypes.string,
  uuid: PropTypes.string.isRequired,
  claimed: PropTypes.bool,
  state: PropTypes.oneOf(['added', 'modified', 'deleted']),
};

// TODO: refactor this props since files isn't always needed
export const fileTypePropTypes = {
  name: PropTypes.string.isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)),
  extensions: PropTypes.arrayOf(PropTypes.string).isRequired,
  allowMultipleFiles: PropTypes.bool.isRequired,
  id: PropTypes.number.isRequired,
};

export async function uploadFile(url, file, onUploadProgress) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const {data} = await indicoAxios.post(url, formData, {
      headers: {'content-type': 'multipart/form-data'},
      onUploadProgress,
    });
    return data;
  } catch (e) {
    handleAxiosError(e);
    return null;
  }
}

export async function uploadAny(url, obj) {
  // TODO: needs a new name, perhaps merge with with the top method
  try {
    const {data} = await indicoAxios.post(url, snakifyKeys(obj));
    return data;
  } catch (e) {
    handleAxiosError(e);
    return null;
  }
}

/**
 * Upload file using axios while triggering all needed actions to update progress.
 *
 * @param {Function} action - the action to be executed after upload is done
 * @param {String} fileTypeId - the id of the File Type
 * @param {Array} acceptedFiles - the "accepted files" array sent by react-dropzone
 * @param {String} uploadCallback - the function to be called on file upload
 * @param {Function} dispatch - the dispatch function for reducer actions
 * @param {String?} fileId - the ID of the file to modify, if any
 * @param {Function} onError - the function to be called on file upload error
 */
export function uploadFiles(
  action,
  fileTypeId,
  acceptedFiles,
  uploadCallback,
  dispatch,
  fileId = null,
  onError = null
) {
  const tmpFileIds = acceptedFiles.map(() => _.uniqueId(_.now()));

  dispatch(actions.startUploads(fileTypeId, acceptedFiles, tmpFileIds));

  return Promise.all(
    _.zip(acceptedFiles, tmpFileIds).map(async ([acceptedFile, tmpFileId]) => {
      const uploadedFile = await uploadCallback(acceptedFile, e =>
        dispatch(actions.progress(fileTypeId, tmpFileId, Math.floor((e.loaded / e.total) * 100)))
      );

      if (uploadedFile === null) {
        // error happened while uploading a file
        dispatch(actions.error(fileTypeId, tmpFileId));
        if (onError) {
          onError();
        }
        return null;
      } else {
        dispatch(
          action(fileTypeId, fileId, tmpFileId, {
            filename: uploadedFile.filename,
            uuid: uploadedFile.uuid,
            claimed: false,
            fileType: fileTypeId,
          })
        );
        return uploadedFile;
      }
    })
  );
}

export async function deleteFile(uuid) {
  try {
    await indicoAxios.delete(deleteFileURL({uuid}));
  } catch (e) {
    handleAxiosError(e);
  }
}

export function mapFileTypes(fileTypes, files) {
  return fileTypes.map(fileType => ({
    ...fileType,
    files: files.filter(file => file.fileType === fileType.id).map(f => ({...f, claimed: true})),
    invalidFiles: [],
  }));
}

export function getFilesFromRevision(fileTypes, revision) {
  return getFiles({fileTypes: mapFileTypes(fileTypes, revision.files)});
}
