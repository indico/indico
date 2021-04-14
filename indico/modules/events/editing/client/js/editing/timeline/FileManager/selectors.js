// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {PluralTranslate} from 'indico/react/i18n';

export const getFiles = state => {
  return _.fromPairs(
    state.fileTypes
      .map(({id, files}) => [
        id,
        files.filter(file => file.state !== 'deleted').map(file => file.uuid),
      ])
      .filter(([, files]) => files.length !== 0)
  );
};

export const isUploading = state => {
  return Object.values(state.uploads).some(uploads => Object.values(uploads).some(x => !x.failed));
};

export const getUploadedFileUUIDs = state => {
  return state.fileTypes.reduce(
    (acc, {files}) =>
      acc.concat(files.filter(f => ['added', 'modified'].includes(f.state)).map(f => f.uuid)),
    []
  );
};

export const getValidationError = createSelector(
  state => state.fileTypes,
  fileTypes => {
    const invalid = fileTypes
      .filter(ft => ft.invalidFiles.some(f => f.length > 0))
      .map(ft => ft.invalidFiles)
      .flat();
    if (invalid.length > 0) {
      return PluralTranslate.string(
        'Invalid file name: {files}',
        'Invalid file names: {files}',
        invalid.length,
        {files: invalid.sort().join(', ')}
      );
    }
    const missing = fileTypes
      .filter(ft => ft.required)
      .filter(ft => !ft.files.some(f => f.state !== 'deleted'))
      .map(ft => ft.name);
    if (!missing.length) {
      return null;
    }
    return PluralTranslate.string(
      'Required file type missing: {types}',
      'Required file types missing: {types}',
      missing.length,
      {types: missing.sort().join(', ')}
    );
  }
);
