// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {fromEvent} from 'file-selector';
import globToRegExp from 'glob-to-regexp';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useCallback, useReducer, useContext, useRef, useMemo, useEffect} from 'react';
import {useDropzone} from 'react-dropzone';
import {Field} from 'react-final-form';
import {Dropdown, Icon, Message, Popup} from 'semantic-ui-react';

import {TooltipIfTruncated} from 'indico/react/components';
import {uploadFile, deleteFile} from 'indico/react/components/files/util';
import {Param, Translate} from 'indico/react/i18n';

import * as actions from './actions';
import FileList from './FileList';
import reducer from './reducer';
import {getFiles, getUploadedFileUUIDs, getValidationError, isUploading} from './selectors';
import Uploads from './Uploads';
import {
  FileManagerContext,
  filePropTypes,
  uploadablePropTypes,
  fileTypePropTypes,
  uploadFiles,
  uploadExistingFile,
  mapFileTypes,
  getFileToDelete,
} from './util';

import './FileManager.module.scss';

export function Dropzone({
  uploadURL,
  fileType: {id, allowMultipleFiles, extensions, filenameTemplate},
  files,
}) {
  const dispatch = useContext(FileManagerContext);
  // we only want to modify the existing file if we do not allow multiple files and
  // there is exactly one file that is not in the 'added' state (which would imply
  // a freshly uploaded file which can be simply replaced)
  const fileToReplace =
    !allowMultipleFiles && files.length && files[0].state !== 'added' ? files[0] : null;
  const fileToDelete = getFileToDelete(files, allowMultipleFiles);
  // as far as the user is concerned, they upload a "new" file when there are no files or
  // multiple files are supported for the file type
  const showNewFileIcon = files.length === 0 || allowMultipleFiles;

  const onDropAccepted = useCallback(
    async acceptedFiles => {
      if (!allowMultipleFiles) {
        acceptedFiles = acceptedFiles.splice(0, 1);
      }
      const rv = await uploadFiles({
        action: fileToReplace ? actions.markModified : actions.markUploaded,
        fileTypeId: id,
        acceptedFiles,
        uploadFunc: uploadFile.bind(null, uploadURL),
        dispatch,
        replaceFileId: fileToReplace ? fileToReplace.uuid : null,
      });
      // only delete if there is a file to delete and the upload of a new file didn't fail
      if (fileToDelete && rv[0] !== null) {
        // we're modifying a freshly uploaded file, so we can get rid of the current one
        deleteFile(fileToDelete.uuid);
      }
    },
    [fileToReplace, fileToDelete, allowMultipleFiles, id, uploadURL, dispatch]
  );

  const {getRootProps, getInputProps, isDragActive} = useDropzone({
    onDropAccepted,
    multiple: allowMultipleFiles,
    accept: extensions.map(ext => `.${ext}`).join(','),
    getFilesFromEvent: async event => {
      const eventFiles = await fromEvent(event);
      if (!filenameTemplate) {
        return eventFiles;
      }

      const templateRe = globToRegExp(filenameTemplate);
      return eventFiles.filter(file => {
        if (file.name === undefined) {
          // most likely the file is just being dragged over and hasn't been dropped yet.
          // in that case only its type is available but not the name
          return true;
        }
        const filename = file.name.slice(0, file.name.lastIndexOf('.'));
        if (!templateRe.test(filename)) {
          dispatch(actions.invalidTemplate(id, file.name));
          return false;
        }
        return true;
      });
    },
  });

  return (
    <div {...getRootProps()}>
      <input {...getInputProps()} />
      <div styleName="dropzone" className={isDragActive ? 'active' : ''}>
        <Icon color="grey" size="big" name={showNewFileIcon ? 'plus circle' : 'exchange'} />
      </div>
    </div>
  );
}

Dropzone.propTypes = {
  uploadURL: PropTypes.string.isRequired,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)),
};

Dropzone.defaultProps = {
  files: [],
};

function FileType({
  uploadURL,
  uploadExistingURL,
  fileType,
  files,
  uploads,
  dispatch,
  uploadableFiles,
}) {
  const ref = useRef(null);
  const fileToDelete = getFileToDelete(files, fileType.allowMultipleFiles);
  const onChangeDropdown = async (__, {value: fileIdx}) => {
    const rv = await uploadFiles({
      action: actions.markUploaded,
      fileTypeId: fileType.id,
      // Use a fake file handle to seamlessly refer to an existing uploadable
      acceptedFiles: [new File([], uploadableFiles[fileIdx].filename)],
      uploadFunc: uploadExistingFile.bind(null, uploadExistingURL, uploadableFiles[fileIdx]),
      dispatch,
      fileId: uploadableFiles[fileIdx].id,
    });
    if (fileToDelete && rv[0] !== null) {
      deleteFile(fileToDelete.uuid);
    }
  };

  return (
    <div styleName="file-type">
      <h3>
        {fileType.name}
        {fileType.required && (
          <Popup
            position="bottom center"
            content={<Translate>This file type is required</Translate>}
            trigger={
              <Icon corner="top right" name="asterisk" color={files.length ? 'black' : 'red'} />
            }
          />
        )}
      </h3>
      <FileRequirements fileType={fileType} />
      <FileList files={files} fileType={fileType} uploadURL={uploadURL} />
      {!_.isEmpty(uploads) && <Uploads uploads={uploads} />}
      {!_.isEmpty(fileType.invalidFiles) && (
        <div style={{paddingBottom: '1em'}}>
          {fileType.invalidFiles.map(invalidFile => (
            <Popup
              position="right center"
              key={`${invalidFile}-${Date.now()}`}
              content={
                <Translate>
                  This file does not conform to the filename template{' '}
                  <Param name="template" value={fileType.filenameTemplate} wrapper={<code />} />
                </Translate>
              }
              trigger={
                <Message
                  onDismiss={() => {
                    dispatch(actions.removeInvalidFilename(fileType.id, invalidFile));
                  }}
                >
                  <Icon name="ban" color="orange" />
                  {invalidFile}
                </Message>
              }
            />
          ))}
        </div>
      )}
      <div styleName="outer-dropzone">
        {uploadableFiles && uploadableFiles.length > 0 && (
          <Dropdown
            className="primary"
            style={{marginBottom: '1em'}}
            text={Translate.string('Use an existing file')}
            options={uploadableFiles.map((uf, i) => ({
              text: uf.filename,
              value: i,
              disabled: files.some(f => f.id === uf.id),
            }))}
            onChange={onChangeDropdown}
            selectOnNavigation={false}
            selectOnBlur={false}
            value={null}
          />
        )}
        <Dropzone dropzoneRef={ref} fileType={fileType} files={files} uploadURL={uploadURL} />
      </div>
    </div>
  );
}

FileType.propTypes = {
  uploadURL: PropTypes.string.isRequired,
  uploadExistingURL: PropTypes.string,
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)),
  uploads: PropTypes.objectOf(
    PropTypes.shape({
      file: PropTypes.object.isRequired,
      progress: PropTypes.number,
    })
  ),
  dispatch: PropTypes.func.isRequired,
  uploadableFiles: PropTypes.arrayOf(PropTypes.shape(uploadablePropTypes)),
};

FileType.defaultProps = {
  files: [],
  uploads: {},
  uploadableFiles: [],
  uploadExistingURL: null,
};

function FileRequirements({fileType}) {
  let extensionInfo = null;
  let templateInfo = null;
  if (fileType.filenameTemplate !== null) {
    const pattern = fileType.filenameTemplate;
    const extension = fileType.extensions.length === 1 ? fileType.extensions[0] : '*';
    templateInfo = (
      <Translate>
        Filename pattern:{' '}
        <Param name="pattern" wrapper={<code />} value={`${pattern}.${extension}`} />
      </Translate>
    );
  }
  if (
    fileType.extensions.length > 1 ||
    (fileType.extensions.length !== 0 && fileType.filenameTemplate === null)
  ) {
    extensionInfo = fileType.extensions.join(', ');
  }
  return (
    <>
      {extensionInfo && (
        <TooltipIfTruncated>
          <div styleName="file-requirements">{extensionInfo}</div>
        </TooltipIfTruncated>
      )}
      {templateInfo && (
        <TooltipIfTruncated>
          <div styleName="file-requirements">{templateInfo}</div>
        </TooltipIfTruncated>
      )}
    </>
  );
}

FileRequirements.propTypes = {
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
};

export default function FileManager({
  onChange,
  uploadURL,
  uploadExistingURL,
  fileTypes,
  files,
  finalFieldName,
  pristine,
  mustChange,
  uploadableFiles,
}) {
  const lastPristineRef = useRef(pristine);
  const _fileTypes = useMemo(() => mapFileTypes(fileTypes, files, uploadableFiles), [
    fileTypes,
    files,
    uploadableFiles,
  ]);
  const [state, dispatch] = useReducer(reducer, {
    fileTypes: _fileTypes,
    uploads: {},
    isDirty: false,
  });

  useEffect(() => {
    // when the pristine flag changes from false to true, it indicates that the form has
    // been reset (or that the user undid their change, but this is not a problem here).
    // in this case we delete all uploaded files and revert to the initial state, which is
    // based on the value coming from the outside.
    //
    // while this is quite ugly, making the FileManager a fully controlled component is even
    // messier, since we'd need to fetch extra file metadata from the server and keep the
    // external state (value) in sync with the local state, which is not trivial at all.
    if (pristine && !lastPristineRef.current) {
      getUploadedFileUUIDs(state).forEach(uuid => deleteFile(uuid));
      dispatch(actions.reset(_fileTypes));
    }
    lastPristineRef.current = pristine;
  }, [pristine, _fileTypes, state]);

  useEffect(() => {
    if (state.isDirty) {
      onChange(getFiles(state));
      dispatch(actions.clearDirty());
    }
  }, [onChange, state]);

  const uploading = isUploading(state);
  const validationError = getValidationError(state);
  return (
    <div styleName="file-manager-wrapper">
      <div styleName="file-manager">
        <FileManagerContext.Provider value={dispatch}>
          {state.fileTypes.map(fileType => (
            <FileType
              key={fileType.id}
              uploadURL={uploadURL}
              uploadExistingURL={uploadExistingURL}
              fileType={fileType}
              files={fileType.files}
              uploads={state.uploads[fileType.id]}
              dispatch={dispatch}
              uploadableFiles={fileType.uploadableFiles}
            />
          ))}
        </FileManagerContext.Provider>
        {!!finalFieldName && uploading && (
          <Field
            name={`_${finalFieldName}_uploading`}
            validate={() => Translate.string('Upload in progress')}
            render={() => null}
          />
        )}
        {!!finalFieldName && validationError && (
          <Field
            name={`_${finalFieldName}_invalid`}
            validate={() => validationError}
            render={() => null}
          />
        )}
        {!!finalFieldName && pristine && mustChange && (
          <Field
            name={`_${finalFieldName}_pristine`}
            validate={() => Translate.string('No changes yet')}
            render={() => null}
          />
        )}
      </div>
    </div>
  );
}

FileManager.propTypes = {
  uploadURL: PropTypes.string.isRequired,
  uploadExistingURL: PropTypes.string,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)),
  onChange: PropTypes.func.isRequired,
  finalFieldName: PropTypes.string,
  pristine: PropTypes.bool,
  mustChange: PropTypes.bool,
  uploadableFiles: PropTypes.arrayOf(PropTypes.shape(uploadablePropTypes)),
};

FileManager.defaultProps = {
  uploadExistingURL: null,
  files: [],
  finalFieldName: null,
  pristine: null,
  mustChange: false,
  uploadableFiles: [],
};

export function FinalFileManager({
  name,
  uploadURL,
  uploadExistingURL,
  fileTypes,
  files,
  mustChange,
  uploadableFiles,
  ...rest
}) {
  // We do not use FinalField here since the file manager is more "standalone"
  // and thus not wrapped in the usual SUI field markup.
  return (
    <Field name={name} isEqual={_.isEqual} format={v => v} parse={v => v} {...rest}>
      {({input, meta: {pristine}}) => (
        <FileManager
          onChange={input.onChange}
          uploadURL={uploadURL}
          uploadExistingURL={uploadExistingURL}
          fileTypes={fileTypes}
          finalFieldName={input.name}
          files={files}
          pristine={pristine}
          mustChange={mustChange}
          uploadableFiles={uploadableFiles}
        />
      )}
    </Field>
  );
}

FinalFileManager.propTypes = {
  name: PropTypes.string.isRequired,
  uploadURL: PropTypes.string.isRequired,
  uploadExistingURL: PropTypes.string,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)),
  mustChange: PropTypes.bool,
  uploadableFiles: PropTypes.arrayOf(PropTypes.shape(uploadablePropTypes)),
};

FinalFileManager.defaultProps = {
  uploadExistingURL: null,
  mustChange: false,
  files: [],
  uploadableFiles: [],
};
