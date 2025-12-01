// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useReducer, useCallback, useEffect} from 'react';
import {
  useDropzone,
  type DropzoneOptions,
  type DropEvent,
  type FileRejection,
} from 'react-dropzone';
import {Field} from 'react-final-form';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {SingleFileArea} from './FileArea';

const DropState = {
  initial: 'initial',
  processing: 'processing',
  finished: 'finished',
  error: 'error',
} as const;

type DropPhase = (typeof DropState)[keyof typeof DropState];

interface DropReducerState {
  file: {filename: string; size: number} | null;
  state: DropPhase;
  errors: string[] | null;
}

type DropReducerAction =
  | {type: 'START'; file: File}
  | {type: 'FINISH'}
  | {type: 'FAIL'; file: File; errors: string[] | null}
  | {type: 'RESET'};

const initialState: DropReducerState = {
  file: null,
  state: DropState.initial,
  errors: null,
};

const dropReducer = (state: DropReducerState, action: DropReducerAction): DropReducerState => {
  switch (action.type) {
    case 'START':
      return {
        file: {
          filename: action.file.name,
          size: action.file.size,
        },
        state: DropState.processing,
        errors: null,
      };
    case 'FINISH':
      return {...state, state: DropState.finished, errors: null};
    case 'FAIL':
      return {
        file: {
          filename: action.file.name,
          size: action.file.size,
        },
        state: DropState.error,
        errors: action.errors,
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
};

const buildFile = (state: DropReducerState) => {
  if (!state.file) {
    return null;
  }

  return {
    filename: state.file.filename,
    size: state.file.size,
    upload: {
      ongoing: state.state === DropState.processing,
      finished: state.state === DropState.finished,
      failed: state.state === DropState.error,
      progress: state.state === DropState.finished ? 100 : 0,
    },
  };
};

interface DropResult<Value = unknown> {
  value?: Value | null;
  errors?: string[] | null;
}

type DropAcceptedHandler<Value = unknown> = (
  file: File
) => Promise<DropResult<Value> | undefined> | DropResult<Value> | undefined;

type DropRejectedHandler<Value = unknown> = (
  rejections: FileRejection[]
) => DropResult<Value> | undefined;

function SingleFileDrop<Value = unknown>({
  onChange,
  onFocus,
  onBlur,
  disabled = false,
  dropzoneOptions = {},
  setValidationError,
  onDropAccepted,
  onDropRejected,
}: {
  onChange: (value: Value | null) => void;
  onFocus: () => void;
  onBlur: () => void;
  disabled?: boolean;
  dropzoneOptions?: Partial<DropzoneOptions>;
  setValidationError?: (message?: string) => void;
  onDropAccepted: DropAcceptedHandler<Value>;
  onDropRejected?: DropRejectedHandler<Value>;
}) {
  const [dropState, dispatch] = useReducer(dropReducer, initialState);

  const markTouched = () => {
    onFocus();
    onBlur();
  };

  const reset = () => {
    dispatch({type: 'RESET'});
    onChange(null);
  };

  const handleDropAccepted = useCallback(
    async ([file]: File[]) => {
      dispatch({type: 'START', file});
      try {
        const {value: newValue = null, errors = null} = (await onDropAccepted(file)) || {};
        onChange(newValue);
        if (errors?.length) {
          dispatch({type: 'FAIL', file, errors});
        } else {
          dispatch({type: 'FINISH'});
        }
      } catch {
        dispatch({
          type: 'FAIL',
          file,
          errors: [Translate.string('Processing the file failed.')],
        });
        onChange(null);
      }
    },
    [onDropAccepted, onChange]
  );

  const handleDropRejected = useCallback(
    (rejections: FileRejection[]) => {
      if (!rejections.length) {
        return;
      }
      const [first] = rejections;
      const result = onDropRejected ? onDropRejected(rejections) : null;
      const errors = (result?.errors && result.errors.length && result.errors) || [
        Translate.string('Please upload a valid file.'),
      ];
      const nextValue = result?.value === undefined ? null : result.value;
      dispatch({
        type: 'FAIL',
        file: first.file,
        errors,
      });
      onChange(nextValue);
    },
    [onDropRejected, onChange]
  );

  const {onDragEnter, onFileDialogCancel, onDrop, ...restDropzoneOptions} = dropzoneOptions;

  const dropzone = useDropzone({
    onDragEnter: (event: DropEvent) => {
      markTouched();
      onDragEnter?.(event as Parameters<NonNullable<DropzoneOptions['onDragEnter']>>[0]);
    },
    onFileDialogCancel: () => {
      markTouched();
      onFileDialogCancel?.();
    },
    onDrop: (acceptedFiles, fileRejections, event) => {
      markTouched();
      if (onDrop) {
        onDrop(acceptedFiles, fileRejections, event);
      }
    },
    onDropAccepted: handleDropAccepted,
    onDropRejected: handleDropRejected,
    disabled: disabled || dropState.state === DropState.processing,
    multiple: false,
    noClick: true,
    noKeyboard: true,
    ...restDropzoneOptions,
  });

  const fileAction = !disabled && dropState.file ? {onClick: reset, icon: 'undo'} : null;

  const file = buildFile(dropState);

  useEffect(() => {
    if (!setValidationError) {
      return;
    }

    if (dropState.state === DropState.processing) {
      setValidationError(Translate.string('Processing file'));
    } else if (dropState.state === DropState.error && dropState.errors?.length) {
      setValidationError(Translate.string('Processing failed'));
    } else {
      setValidationError(undefined);
    }
  }, [dropState.state, dropState.errors, setValidationError]);

  return (
    <SingleFileArea
      dropzone={dropzone}
      file={file}
      fileAction={fileAction}
      errors={dropState.errors}
    />
  );
}

export default function FinalSingleFileDrop({
  name,
  ...rest
}: {
  name: string;
  onDropAccepted: DropAcceptedHandler;
  onDropRejected?: DropRejectedHandler;
  dropzoneOptions?: Partial<DropzoneOptions>;
  [key: string]: unknown;
}) {
  return (
    <Field
      name={`_${name}_invalidator`}
      validate={value => value || undefined}
      subscription={{value: true}}
      render={({input: {onChange: setValidationError}}) => (
        <FinalField
          name={name}
          component={SingleFileDrop}
          setValidationError={setValidationError}
          {...rest}
        />
      )}
    />
  );
}

export {SingleFileDrop};
