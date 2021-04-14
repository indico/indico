// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const MARK_UPLOADED = 'MARK_UPLOADED';
export const MARK_DELETED = 'MARK_DELETED';
export const MARK_MODIFIED = 'MARK_MODIFIED';
export const UNDELETE = 'UNDELETE';
export const REVERT = 'REVERT';
export const PROGRESS = 'PROGRESS';
export const START_UPLOADS = 'START_UPLOADS';
export const CLEAR_DIRTY = 'CLEAR_DIRTY';
export const UPLOAD_ERROR = 'UPLOAD_ERROR';
export const RESET = 'RESET';
export const INVALID_TEMPLATE = 'INVALID_TEMPLATE';
export const REMOVE_INVALID_FILENAME = 'REMOVE_INVALID_FILENAME';

export const startUploads = (fileTypeId, files, tmpFileIds) => ({
  type: START_UPLOADS,
  tmpFileIds,
  files,
  fileTypeId,
});

export const progress = (fileTypeId, tmpFileId, percent) => ({
  type: PROGRESS,
  tmpFileId,
  fileTypeId,
  percent,
});

export const markModified = (fileTypeId, fileId, tmpFileId, file) => ({
  type: MARK_MODIFIED,
  fileId,
  fileTypeId,
  file,
  tmpFileId,
});

export const markDeleted = (fileTypeId, fileId) => ({
  type: MARK_DELETED,
  fileTypeId,
  fileId,
});

export const undelete = (fileTypeId, fileId) => ({
  type: UNDELETE,
  fileTypeId,
  fileId,
});

export const revert = (fileTypeId, fileId) => ({
  type: REVERT,
  fileTypeId,
  fileId,
});

export const markUploaded = (fileTypeId, fileId, tmpFileId, file) => ({
  type: MARK_UPLOADED,
  fileTypeId,
  fileId,
  tmpFileId,
  file,
});

export const clearDirty = () => ({
  type: CLEAR_DIRTY,
});

export const error = (fileTypeId, tmpFileId) => ({
  type: UPLOAD_ERROR,
  fileTypeId,
  tmpFileId,
});

export const reset = fileTypes => ({
  type: RESET,
  fileTypes,
});

export const invalidTemplate = (fileTypeId, filename) => ({
  type: INVALID_TEMPLATE,
  fileTypeId,
  filename,
});

export const removeInvalidFilename = (fileTypeId, filename) => ({
  type: REMOVE_INVALID_FILENAME,
  fileTypeId,
  filename,
});
