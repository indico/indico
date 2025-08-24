// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useReducer, useEffect} from 'react';
import {useDropzone} from 'react-dropzone';
import {Field} from 'react-final-form';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {SingleFileArea} from './FileArea';
import {fileDetailsShape} from './props';
import {deleteFile, uploadFile, UploadState} from './util';

function reducer(state, action) {
  switch (action.type) {
    case 'PROGRESS':
      return {...state, progress: action.percent};
    case 'START_UPLOAD':
      return {
        ...state,
        progress: 0,
        file: {
          filename: action.file.name,
          size: action.file.size,
          uuid: null,
        },
        state: UploadState.uploading,
        errors: null,
      };
    case 'UPLOAD_FINISHED':
      return {
        ...state,
        file: {
          filename: action.file.filename,
          size: action.file.size,
          uuid: action.file.uuid,
        },
        state: UploadState.finished,
        errors: null,
      };
    case 'UPLOAD_FAILED':
      return {
        ...state,
        state: UploadState.error,
        errors: action.errors,
      };
    case 'RESET':
      return {
        ...state,
        state: UploadState.initial,
        file: null,
        errors: null,
      };
  }
}

const initialState = {
  progress: 0,
  file: null,
  state: UploadState.initial,
};

const SingleFileManager = ({
  value,
  required,
  disabled,
  onChange,
  onFocus,
  onBlur,
  setValidationError,
  initialFileDetails,
  validExtensions,
  uploadURL,
}) => {
  const [uploadState, dispatch] = useReducer(reducer, initialState);

  const isInitialFile = uploadState.state === UploadState.initial;
  const isUploading = uploadState.state === UploadState.uploading;
  const uploadFinished = uploadState.state === UploadState.finished;
  const uploadFailed = uploadState.state === UploadState.error;

  const markTouched = () => {
    onFocus();
    onBlur();
  };

  const deleteUploadedFile = useCallback(() => {
    if (uploadFinished) {
      deleteFile(uploadState.file.uuid);
    }
  }, [uploadFinished, uploadState.file]);

  const reset = () => {
    deleteUploadedFile();
    dispatch({type: 'RESET'});
    onChange(initialFileDetails ? initialFileDetails.uuid : null);
  };

  const clear = () => {
    deleteUploadedFile();
    dispatch({type: 'RESET'});
    onChange(null);
  };

  const onDropAccepted = useCallback(
    async ([file]) => {
      deleteUploadedFile();
      dispatch({type: 'START_UPLOAD', file});
      const {data, errors} = await uploadFile(uploadURL, file, e =>
        dispatch({
          type: 'PROGRESS',
          percent: Math.floor((e.loaded / e.total) * 100),
        })
      );
      if (data) {
        dispatch({type: 'UPLOAD_FINISHED', file: data});
        onChange(data.uuid);
      } else {
        dispatch({type: 'UPLOAD_FAILED', errors});
        onChange(null);
      }
    },
    [deleteUploadedFile, uploadURL, onChange]
  );

  const dropzone = useDropzone({
    onDragEnter: markTouched,
    onFileDialogCancel: markTouched,
    onDrop: markTouched,
    onDropAccepted,
    disabled: disabled || isUploading || uploadFailed,
    accept: validExtensions ? validExtensions.map(ext => `.${ext}`) : null,
    multiple: false,
    noClick: true,
    noKeyboard: true,
  });

  let file = null;
  if (!isInitialFile && (uploadState.file.uuid === null || uploadState.file.uuid === value)) {
    // a file is currently being uploaded (no uuid) or has been uploaded and matches the
    // current value of the field (as stored in final-form)
    file = {
      filename: uploadState.file.filename,
      size: uploadState.file.size,
      upload: {
        failed: uploadFailed,
        ongoing: isUploading,
        finished: uploadFinished,
        progress: uploadState.progress,
      },
    };
  } else if (initialFileDetails !== null && value === initialFileDetails.uuid) {
    // we have an initial file and the final-form field value points to it
    file = initialFileDetails;
  }

  // we let the user reset/clear the field if:
  // - their upload failed (this goes back to the initial file)
  // - the field is not required and there is a file (this clears the field)
  let fileAction = null;
  if (disabled) {
    // if the field is disabled for some reason we never show an action
  } else if (uploadFailed || uploadFinished) {
    fileAction = {onClick: reset, icon: 'undo'};
  } else if (isInitialFile && !required) {
    fileAction = {onClick: clear, icon: 'x', color: 'red'};
  }

  useEffect(() => {
    if (!setValidationError) {
      return;
    }
    // we need to make the form invalid during these states, but can't do that through
    // a normal validator since it only acts on the field value. so we wrap the whole
    // component in a separate final-form field and then set that field's value to the
    // error message (which in turn is returned by the validator of that field as a
    // validation error)
    if (isUploading) {
      setValidationError(Translate.string('Upload in progress'));
    } else if (uploadFailed) {
      setValidationError(Translate.string('Upload failed'));
    } else {
      // must be undefined since it goes into the fake field's value and we do not want
      // anything included in the values that end up getting submitted
      setValidationError(undefined);
    }
  }, [setValidationError, isUploading, uploadFailed]);

  return (
    <SingleFileArea
      dropzone={dropzone}
      file={file}
      fileAction={fileAction}
      errors={uploadState.errors}
    />
  );
};

SingleFileManager.propTypes = {
  value: PropTypes.string,
  disabled: PropTypes.bool.isRequired,
  required: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  setValidationError: PropTypes.func,
  initialFileDetails: fileDetailsShape,
  validExtensions: PropTypes.arrayOf(PropTypes.string),
  uploadURL: PropTypes.string.isRequired,
};

SingleFileManager.defaultProps = {
  value: null,
  setValidationError: null,
  initialFileDetails: null,
  validExtensions: null,
};

export default function FinalSingleFileManager({name, ...rest}) {
  return (
    <Field
      name={`_${name}_invalidator`}
      validate={value => value || undefined}
      render={({input: {onChange: setDummyValue}}) => (
        <FinalField
          name={name}
          component={SingleFileManager}
          setValidationError={setDummyValue}
          {...rest}
        />
      )}
    />
  );
}

FinalSingleFileManager.propTypes = {
  name: PropTypes.string.isRequired,
  uploadURL: PropTypes.string.isRequired,
  initialFileDetails: fileDetailsShape,
  validExtensions: PropTypes.arrayOf(PropTypes.string),
};

FinalSingleFileManager.defaultProps = {
  initialFileDetails: null,
  validExtensions: null,
};
