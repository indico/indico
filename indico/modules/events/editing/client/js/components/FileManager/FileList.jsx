// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useContext, useRef} from 'react';
import PropTypes from 'prop-types';
import Dropzone from 'react-dropzone';
import {Icon} from 'semantic-ui-react';
import {FileManagerContext, filePropTypes} from './util';
import styles from './FileManager.module.scss';

export default function FileList({files, fileTypeId, multiple}) {
  const dispatch = useContext(FileManagerContext);
  const ref = useRef(null);

  function onModifyDrop(fileId) {
    return acceptedFiles => {
      dispatch({
        type: 'MODIFY',
        fileTypeId,
        fileId,
        file: {name: acceptedFiles[0].name, id: 'file2', url: 'file2url', claimed: false},
      });
    };
  }

  return (
    <ul styleName="file-list">
      {files.map(({name, id, state}) => (
        <li key={id} styleName="file-row">
          <span className={`${styles['file-state']} ${state || ''}`}>{name}</span>
          <span>
            {!state && multiple && (
              <>
                <Icon
                  styleName="exchange-icon"
                  name="exchange"
                  onClick={() => {
                    ref.current.open();
                  }}
                />
                <Dropzone ref={ref} onDrop={onModifyDrop(id)}>
                  {({getRootProps, getInputProps}) => (
                    <span {...getRootProps()}>
                      <input {...getInputProps()} />
                    </span>
                  )}
                </Dropzone>
              </>
            )}
            {state !== 'deleted' && state !== 'modified' && (
              <Icon
                styleName="delete-icon"
                onClick={() => dispatch(actions.markDeleted(fileTypeId, id))}
                name="trash"
              />
            )}
            {state === 'deleted' && (
              <Icon
                styleName="undo-icon"
                onClick={() => dispatch(actions.undelete(fileTypeId, id))}
                name="undo"
              />
            )}
            {state === 'modified' && (
              <Icon
                styleName="undo-icon"
                onClick={() => dispatch(actions.revert(fileTypeId, id))}
                name="undo"
              />
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}

FileList.propTypes = {
  files: filePropTypes.isRequired,
  fileTypeId: PropTypes.string.isRequired,
  multiple: PropTypes.bool.isRequired,
};
