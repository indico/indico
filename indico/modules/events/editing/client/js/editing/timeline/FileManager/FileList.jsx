// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useContext, useCallback, useState} from 'react';
import {useDropzone} from 'react-dropzone';
import {Icon, Popup} from 'semantic-ui-react';

import {TooltipIfTruncated} from 'indico/react/components';
import {uploadFile, deleteFile} from 'indico/react/components/files/util';
import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {FileManagerContext, filePropTypes, uploadFiles, fileTypePropTypes} from './util';

import './FileManager.module.scss';

function FileAction({onClick, active, icon, className, popupContent}) {
  const trigger = (
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

  return <Popup position="bottom center" content={popupContent} trigger={trigger} />;
}

FileAction.propTypes = {
  onClick: PropTypes.func.isRequired,
  active: PropTypes.bool.isRequired,
  icon: PropTypes.string.isRequired,
  className: PropTypes.string.isRequired,
  popupContent: PropTypes.string.isRequired,
};

function FileEntry({uploadURL, fileType, file: {uuid, filename, state, claimed, downloadURL}}) {
  const dispatch = useContext(FileManagerContext);
  const [activeButton, setActiveButton] = useState(null);

  const onDropAccepted = useCallback(
    async acceptedFiles => {
      setActiveButton('replace');
      await uploadFiles({
        fileTypeId: fileType.id,
        acceptedFiles: acceptedFiles.map(file => ({file, replaceFileId: uuid})),
        uploadFunc: uploadFile.bind(null, uploadURL),
        dispatch,
        onError: () => setActiveButton(null),
      });
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
      <TooltipIfTruncated>
        <span styleName="file-state" className={state || ''}>
          {downloadURL ? (
            <a href={downloadURL} target="_blank" rel="noopener noreferrer">
              {filename}
            </a>
          ) : (
            filename
          )}
        </span>
      </TooltipIfTruncated>
      <span>
        {!state && fileType.allowMultipleFiles && (
          <>
            <FileAction
              icon="exchange"
              styleName="exchange-icon"
              popupContent={Translate.string('Replace the existing file')}
              active={activeButton === 'replace'}
              onClick={open}
            />
            <span {...getRootProps()}>
              <input {...getInputProps()} />
            </span>
          </>
        )}
        {state !== 'deleted' && state !== 'modified' ? (
          <FileAction
            icon="trash"
            styleName="delete-icon"
            popupContent={Translate.string('Delete the existing file')}
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
            styleName="undo-icon"
            popupContent={Translate.string('Revert to the existing file')}
            active={activeButton === 'undo'}
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
