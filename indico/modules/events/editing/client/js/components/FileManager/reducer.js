// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

export default function reducer(state, action) {
  const fileType = _.find(state, {id: action.fileTypeId});
  switch (action.type) {
    case 'UPLOAD':
      action.file.state = 'added';
      if (fileType.multiple) {
        fileType.files = fileType.files.concat(action.file);
      } else {
        fileType.files = [action.file];
      }
      return [...state];

    case 'DELETE': {
      const file = _.find(fileType.files, {id: action.fileId});
      if (file.claimed) {
        file.state = 'deleted';
      } else {
        _.pull(fileType.files, file);
      }
      return [...state];
    }

    case 'MODIFY': {
      const originalFile = _.find(fileType.files, {id: action.fileId});
      fileType.files = fileType.files.map(file => {
        if (file.id === action.fileId) {
          return {state: 'modified', originalFile, ...action.file};
        } else {
          return file;
        }
      });
      return [...state];
    }

    case 'UNDELETE': {
      const file = _.find(fileType.files, {id: action.fileId});
      file.state = null;
      return [...state];
    }

    case 'REVERT': {
      fileType.files = fileType.files.map(file => {
        if (file.id === action.fileId) {
          return {state: null, ...file.originalFile};
        } else {
          return file;
        }
      });
      return [...state];
    }
  }
}
