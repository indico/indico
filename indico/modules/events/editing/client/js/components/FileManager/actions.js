// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
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
