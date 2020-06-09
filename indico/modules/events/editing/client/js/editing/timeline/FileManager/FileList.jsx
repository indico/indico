// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useContext, useCallback, useState} from 'react';
import PropTypes from 'prop-types';
import {useDropzone} from 'react-dropzone';
import {Icon} from 'semantic-ui-react';
import {
  FileManagerContext,
  filePropTypes,
  uploadFiles,
  uploadFile,
  deleteFile,
  fileTypePropTypes,
} from './util';
import * as actions from './actions';

import './FileManager.module.scss';

function FileAction({onClick, active, icon, className}) {
  return (
    <Icon
      className={className}
      name={active ? 'spinner' : icon}
      loading={active}
      onClick={() => {
        if (!active) {
          onClick();
        }
      }}
    />
  );
}

FileAction.propTypes = {
  onClick: PropTypes.func.isRequired,
  active: PropTypes.bool.isRequired,
  icon: PropTypes.string.isRequired,
  className: PropTypes.string.isRequired,
};

function FileEntry({uploadURL, fileType, file: {uuid, filename, state, claimed, downloadURL}}) {
  const dispatch = useContext(FileManagerContext);
  const [activeButton, setActiveButton] = useState(null);

  const onDropAccepted = useCallback(
    async acceptedFiles => {
      setActiveButton('replace');
      await uploadFiles(
        actions.markModified,
        fileType.id,
        acceptedFiles,
        uploadFile.bind(null, uploadURL),
        dispatch,
        uuid,
        () => setActiveButton(null)
      );
      // when we're done, the component will have been unmounted,
      // so there's no need to unset the active button
    },
    [dispatch, uploadURL, uuid, fileType.id]
  );

  const {getRootProps, getInputProps, open} = useDropzone({
    onDropAccepted,
    multiple: fileType.allowMultipleFiles,
    accept: fileType.extensions.map(ext => `.${ext}`).join(','),
  });

  return (
    <>
      <span styleName="file-state" className={state || ''}>
        {downloadURL ? (
          <a href={downloadURL} target="_blank" rel="noopener noreferrer">
            {filename}
          </a>
        ) : (
          filename
        )}
      </span>
      <span>
        {!state && fileType.allowMultipleFiles && (
          <>
            <FileAction
              icon="exchange"
              active={activeButton === 'replace'}
              styleName="exchange-icon"
              onClick={open}
            />
            <span {...getRootProps()}>
              <input {...getInputProps()} />
            </span>
          </>
        )}
        {state !== 'deleted' && state !== 'modified' ? (
          <FileAction
            styleName="delete-icon"
            icon="trash"
            active={activeButton === 'delete'}
            onClick={async () => {
              if (!claimed) {
                // if the file is not part of the revision yet,
                // we can safely delete it from the server
                setActiveButton('delete');
                await deleteFile(uuid);
                setActiveButton(null);
              }
              dispatch(actions.markDeleted(fileType.id, uuid));
            }}
          />
        ) : (
          <FileAction
            icon="undo"
            active={activeButton === 'undo'}
            styleName="undo-icon"
            onClick={async () => {
              if (!claimed) {
                setActiveButton('undo');
                await deleteFile(uuid);
                setActiveButton(null);
              }
              dispatch(
                (state === 'deleted' ? actions.undelete : actions.revert)(fileType.id, uuid)
              );
            }}
          />
        )}
      </span>
    </>
  );
}

FileEntry.propTypes = {
  uploadURL: PropTypes.string.isRequired,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
  file: PropTypes.shape(filePropTypes).isRequired,
};

export default function FileList({files, fileType, uploadURL}) {
  return (
    <ul styleName="file-list">
      {files.map(file => (
        <li key={file.uuid} styleName="file-row">
          <FileEntry fileType={fileType} uploadURL={uploadURL} file={file} />
        </li>
      ))}
    </ul>
  );
}

FileList.propTypes = {
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
  uploadURL: PropTypes.string.isRequired,
};
