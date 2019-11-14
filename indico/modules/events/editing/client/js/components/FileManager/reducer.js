// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {combineReducers} from 'redux';
import * as actions from './actions';

export default combineReducers({
  fileTypes: (state = [], action) => {
    const fileType = _.find(state, {id: action.fileTypeId});
    switch (action.type) {
      case actions.MARK_UPLOADED:
        action.file.state = 'added';
        if (fileType.multiple) {
          fileType.files = fileType.files.concat(action.file);
        } else {
          fileType.files = [action.file];
        }
        return [...state];

      case actions.MARK_DELETED: {
        const file = _.find(fileType.files, {uuid: action.fileId});
        if (file.claimed) {
          file.state = 'deleted';
        } else {
          _.pull(fileType.files, file);
        }
        return [...state];
      }

      case actions.MARK_MODIFIED: {
        const currentFile = _.find(fileType.files, {uuid: action.fileId});
        fileType.files = fileType.files.map(file => {
          if (file.uuid === action.fileId) {
            return {
              state: 'modified',
              // if the current file is already a "replacement", then let's preserve
              // the "pointer" to the original file (we only allow undo to the initial file)
              originalFile: currentFile.originalFile || currentFile,
              ...action.file,
            };
          } else {
            return file;
          }
        });
        return [...state];
      }

      case actions.UNDELETE: {
        const file = _.find(fileType.files, {uuid: action.fileId});
        file.state = null;
        return [...state];
      }

      case actions.REVERT: {
        fileType.files = fileType.files.map(file => {
          if (file.uuid === action.fileId) {
            return {state: null, ...file.originalFile};
          } else {
            return file;
          }
        });
        return [...state];
      }

      default:
        return state;
    }
  },
  uploads: (state = {}, action) => {
    switch (action.type) {
      case actions.PROGRESS: {
        const fileType = state[action.fileTypeId];
        const tmpFile = fileType[action.tmpFileId];
        return {
          ...state,
          [action.fileTypeId]: {
            ...fileType,
            [action.tmpFileId]: {...tmpFile, percent: action.percent},
          },
        };
      }

      case actions.START_UPLOADS: {
        const newUploads = _.mapValues(_.zipObject(action.tmpFileIds, action.files), file => ({
          progress: 0,
          file,
        }));
        return {...state, [action.fileTypeId]: {...state[action.fileTypeId], ...newUploads}};
      }

      case actions.MARK_MODIFIED:
      case actions.MARK_UPLOADED: {
        const fileType = state[action.fileTypeId];
        return {
          ...state,
          [action.fileTypeId]: _.omit(fileType, action.tmpFileId),
        };
      }

      default:
        return state;
    }
  },
});
