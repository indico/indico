// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadFileURL from 'indico-url:event_editing.file_upload';
import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import * as actions from './actions';

export const FileManagerContext = React.createContext(null);

export const filePropTypes = PropTypes.arrayOf(
  PropTypes.shape({
    name: PropTypes.string.isRequired,
    url: PropTypes.string.isRequired,
    id: PropTypes.string.isRequired,
    claimed: PropTypes.bool.isRequired,
    state: PropTypes.oneOf(['added', 'modified', 'deleted']),
  })
);

async function uploadFile(file, urlParams, onUploadProgress) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const {data} = await indicoAxios.post(uploadFileURL(urlParams), formData, {
      headers: {'content-type': 'multipart/form-data'},
      onUploadProgress,
    });
    return data;
  } catch (e) {
    handleAxiosError(e, false, true);
  }
}

/**
 * Upload file using axios while triggering all needed actions to update progress.
 *
 * @param {Function} action - the action to be executed after upload is done
 * @param {String} fileTypeId - the id of the File Type
 * @param {Array} acceptedFiles - the "accepted files" array sent by react-dropzone
 * @param {String} eventId - the id of the event
 * @param {Function} dispatch - the dispatch function for reducer actions
 * @param {String?} fileId - the ID of the file to modify, if any
 */
export async function uploadFiles(
  action,
  fileTypeId,
  acceptedFiles,
  eventId,
  dispatch,
  fileId = null
) {
  const tmpFileIds = acceptedFiles.map(() => _.uniqueId(_.now()));

  dispatch(actions.startUploads(fileTypeId, acceptedFiles, tmpFileIds));

  _.zip(acceptedFiles, tmpFileIds).forEach(async ([acceptedFile, tmpFileId]) => {
    const uploadedFile = await uploadFile(acceptedFile, {confId: eventId}, e =>
      dispatch(actions.progress(fileTypeId, tmpFileId, Math.floor((e.loaded / e.total) * 100)))
    );
    dispatch(
      action(fileTypeId, fileId, tmpFileId, {
        name: uploadedFile.filename,
        id: uploadedFile.uuid,
        url: null,
        claimed: false,
      })
    );
  });
}
