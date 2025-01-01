// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import deleteFileURL from 'indico-url:files.delete_file';

import {FORM_ERROR} from 'final-form';

import {handleSubmissionError} from 'indico/react/forms';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

export async function uploadFile(url, file, onUploadProgress) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const {data} = await indicoAxios.post(url, formData, {
      headers: {'content-type': 'multipart/form-data'},
      onUploadProgress,
    });
    return {data, errors: null};
  } catch (error) {
    if (error.response?.status === 422) {
      const errors = handleSubmissionError(error, null, {}, false);
      return {data: null, errors: errors.file || errors[FORM_ERROR]};
    }
    return {data: null, errors: [handleAxiosError(error)]};
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
