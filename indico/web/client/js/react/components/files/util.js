// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import deleteFileURL from 'indico-url:files.delete_file';

import _ from 'lodash';

import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

export async function uploadFile(url, file, onUploadProgress) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const {data} = await indicoAxios.post(url, formData, {
      headers: {'content-type': 'multipart/form-data'},
      onUploadProgress,
    });
    return data;
  } catch (error) {
    if (_.get(error, 'response.status') !== 422) {
      handleAxiosError(error);
    }
    return null;
  }
}

export async function deleteFile(uuid) {
  try {
    await indicoAxios.delete(deleteFileURL({uuid}));
  } catch (e) {
    handleAxiosError(e);
  }
}

export const UploadState = {
  initial: 'initial', // no file or the initial file selected
  uploading: 'uploading', // currently uploading a file
  error: 'error', // upload failed
  finished: 'finished', // upload finished (uploaded file is the field's current file)
};
