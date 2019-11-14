// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useContext, useRef, useState} from 'react';
import PropTypes from 'prop-types';
import Dropzone from 'react-dropzone';
import {Icon} from 'semantic-ui-react';
import {FileManagerContext, filePropTypes, uploadFiles, deleteFile} from './util';
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

function FileEntry({
  eventId,
  fileTypeId,
  allowMultipleFiles,
  file: {uuid, filename, state, claimed},
}) {
  const ref = useRef(null);
  const dispatch = useContext(FileManagerContext);
  const [activeButton, setActiveButton] = useState(null);

  return (
    <>
      <span styleName="file-state" className={state || ''}>
        {filename}
      </span>
      <span>
        {!state && allowMultipleFiles && (
          <>
            <FileAction
              icon="exchange"
              active={activeButton === 'replace'}
              styleName="exchange-icon"
              onClick={() => {
                ref.current.open();
              }}
            />
            <Dropzone
              ref={ref}
              onDrop={async acceptedFiles => {
                setActiveButton('replace');
                await uploadFiles(
                  actions.markModified,
                  fileTypeId,
                  acceptedFiles,
                  eventId,
                  dispatch,
                  uuid
                );
              }}
            >
              {({getRootProps, getInputProps}) => (
                <span {...getRootProps()}>
                  <input {...getInputProps()} />
                </span>
              )}
            </Dropzone>
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
              dispatch(actions.markDeleted(fileTypeId, uuid));
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
              dispatch((state === 'deleted' ? actions.undelete : actions.revert)(fileTypeId, uuid));
            }}
          />
        )}
      </span>
    </>
  );
}

FileEntry.propTypes = {
  eventId: PropTypes.string.isRequired,
  fileTypeId: PropTypes.number.isRequired,
  allowMultipleFiles: PropTypes.bool.isRequired,
  file: PropTypes.shape(filePropTypes).isRequired,
};

export default function FileList({files, fileTypeId, allowMultipleFiles, eventId}) {
  return (
    <ul styleName="file-list">
      {files.map(file => (
        <li key={file.uuid} styleName="file-row">
          <FileEntry
            fileTypeId={fileTypeId}
            eventId={eventId}
            allowMultipleFiles={allowMultipleFiles}
            file={file}
          />
        </li>
      ))}
    </ul>
  );
}

FileList.propTypes = {
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
  fileTypeId: PropTypes.number.isRequired,
  allowMultipleFiles: PropTypes.bool.isRequired,
  eventId: PropTypes.string.isRequired,
};
