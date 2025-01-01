// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useReducer, useEffect, useRef, useState} from 'react';
import {useDropzone} from 'react-dropzone';
import {Field} from 'react-final-form';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {fileDetailsShape} from '../files/props';
import {deleteFile, uploadFile} from '../files/util';

import {PictureArea} from './PictureArea';
import {PictureCropper} from './PictureCropper';
import {PictureWebcam} from './PictureWebcam';
import {PictureState} from './util';

function reducer(state, action) {
  switch (action.type) {
    case 'PROGRESS':
      return {...state, progress: action.percent};
    case 'START_UPLOAD':
      return {
        ...state,
        progress: 0,
        picture: {
          filename: action.picture.name,
          size: action.picture.size,
          uuid: null,
        },
        state: PictureState.uploading,
        errors: null,
      };
    case 'START_CAPTURING':
      return {
        ...state,
        state: PictureState.capturing,
      };
    case 'START_EDITING':
      return {
        ...state,
        imageSrc: action.imageSrc,
        state: PictureState.editing,
      };
    case 'UPLOAD_FINISHED':
      return {
        ...state,
        picture: {
          filename: action.picture.filename,
          size: action.picture.size,
          uuid: action.picture.uuid,
        },
        state: PictureState.finished,
        errors: null,
      };
    case 'FAILED':
      return {
        ...state,
        state: PictureState.error,
        errors: action.errors,
      };
    case 'RESET':
      return {
        ...state,
        state: PictureState.initial,
        picture: null,
        errors: null,
      };
  }
}

const initialState = {
  progress: 0,
  picture: null,
  state: PictureState.initial,
  imageSrc: null,
};

const PictureManager = ({
  value,
  required,
  disabled,
  onChange,
  onFocus,
  onBlur,
  setValidationError,
  initialPictureDetails,
  uploadURL,
  previewURL,
  minPictureSize,
}) => {
  // XXX careful, we have `pictureState` (the current state) and `PictureState` (an enum) here...
  const [pictureState, dispatch] = useReducer(reducer, initialState);
  const [picturePreview, setPicturePreview] = useState(null);
  const cameraRef = useRef(null);
  const cropperRef = useRef(null);
  const cameraBackActionRef = useRef(null);
  const cropperBackActionRef = useRef(null);
  const [customFileRejections, setCustomFileRejections] = useState(null);
  const [isCameraAllowed, setIsCameraAllowed] = useState(true);

  const isInitialPicture = pictureState.state === PictureState.initial;
  const isUploading = pictureState.state === PictureState.uploading;
  const isCapturing = pictureState.state === PictureState.capturing;
  const isEditing = pictureState.state === PictureState.editing;
  const uploadFinished = pictureState.state === PictureState.finished;
  const failed = pictureState.state === PictureState.error;
  const errorMessages = pictureState.errors;

  const getPreview = useCallback(() => {
    return isInitialPicture ? previewURL : picturePreview;
  }, [picturePreview, previewURL, isInitialPicture]);

  const deleteUploadedPicture = useCallback(() => {
    if (uploadFinished || (pictureState.picture !== null && pictureState.picture.uuid !== null)) {
      deleteFile(pictureState.picture.uuid);
    }
  }, [uploadFinished, pictureState.picture]);

  const markTouched = () => {
    onFocus();
    onBlur();
  };

  const reset = () => {
    deleteUploadedPicture();
    dispatch({type: 'RESET'});
    onChange(initialPictureDetails ? initialPictureDetails.uuid : null);
  };

  const clear = () => {
    deleteUploadedPicture();
    dispatch({type: 'RESET'});
    onChange(null);
  };

  const onCapture = () => {
    const imageSrc = cameraRef.current.getScreenshot();
    dispatch({type: 'START_EDITING', imageSrc});
  };

  const onCameraMediaError = mediaErr => {
    console.log(mediaErr);
    setIsCameraAllowed(false);
    dispatch({type: 'RESET'});
  };

  useEffect(() => {
    if (uploadFinished) {
      cameraBackActionRef.current = 'finished';
    } else if (isInitialPicture) {
      cameraBackActionRef.current = 'initial';
    }
  }, [uploadFinished, isInitialPicture]);

  const cameraBackAction = () => {
    if (
      cameraBackActionRef.current === 'finished' &&
      (pictureState.picture.uuid === null || pictureState.picture.uuid === value)
    ) {
      dispatch({type: 'UPLOAD_FINISHED', picture: pictureState.picture});
    } else {
      dispatch({type: 'RESET'});
    }
  };

  const Camera = () => (
    <PictureWebcam
      cameraRef={cameraRef}
      onCapture={onCapture}
      onUserMediaError={onCameraMediaError}
      backAction={cameraBackAction}
      minSize={minPictureSize || 0}
    />
  );

  const onOpenCameraDialog = () => {
    setCustomFileRejections(null);
    dispatch({type: 'START_CAPTURING'});
  };

  const uploadPicture = useCallback(
    async file => {
      deleteUploadedPicture();
      dispatch({type: 'START_UPLOAD', picture: file});
      const {data, errors} = await uploadFile(uploadURL, file, e =>
        dispatch({
          type: 'PROGRESS',
          percent: Math.floor((e.loaded / e.total) * 100),
        })
      );
      if (data) {
        dispatch({type: 'UPLOAD_FINISHED', picture: data});
        onChange(data.uuid);
      } else {
        dispatch({type: 'FAILED', errors});
        setPicturePreview(previewURL);
        onChange(null);
      }
    },
    [deleteUploadedPicture, onChange, uploadURL, previewURL]
  );

  const onImageCrop = () => {
    if (cropperRef.current.cropper !== undefined) {
      const settings = {minWidth: 25, minHeight: 25};
      const imageSrc = cropperRef.current.cropper
        .getCroppedCanvas(settings)
        .toDataURL('image/jpeg');
      setPicturePreview(imageSrc);
      markTouched();
      fetch(imageSrc)
        .then(res => res.blob())
        .then(blob => {
          const file = new File([blob], 'picture.jpg', blob);
          uploadPicture(file);
        });
    }
  };

  useEffect(() => {
    if (isCapturing) {
      cropperBackActionRef.current = 'camera';
    } else if (uploadFinished) {
      cropperBackActionRef.current = 'finished';
    } else if (isInitialPicture) {
      cropperBackActionRef.current = 'initial';
    }
  }, [isCapturing, uploadFinished, isInitialPicture]);

  const onOpenEditDialog = () => {
    setCustomFileRejections(null);
    fetch(getPreview())
      .then(res => res.blob())
      .then(blob => dispatch({type: 'START_EDITING', imageSrc: URL.createObjectURL(blob)}));
  };

  const cropBackAction = () => {
    if (cropperBackActionRef.current === 'camera') {
      dispatch({type: 'START_CAPTURING'});
    } else if (
      cropperBackActionRef.current === 'finished' &&
      (pictureState.picture.uuid === null || pictureState.picture.uuid === value)
    ) {
      dispatch({type: 'UPLOAD_FINISHED', picture: pictureState.picture});
    } else {
      dispatch({type: 'RESET'});
    }
  };

  const Cropper = () => (
    <PictureCropper
      cropperRef={cropperRef}
      src={pictureState.imageSrc}
      onCrop={onImageCrop}
      backAction={cropBackAction}
      minCropSize={minPictureSize || 25}
    />
  );

  const onDropAccepted = async ([file]) => {
    const imageSrc = URL.createObjectURL(file);
    const loadImage = src => {
      return new Promise(resolve => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.src = src;
      });
    };
    let rejected = false;
    const img = await loadImage(imageSrc);
    if (minPictureSize && minPictureSize !== 0) {
      if (Math.min(img.naturalWidth, img.naturalHeight) < minPictureSize) {
        setCustomFileRejections([
          Translate.string(
            'The picture you uploaded is {width} by {height} pixels. Please upload a picture with a minimum of {minPictureSize} pixels on its shortest side.',
            {width: img.naturalWidth, height: img.naturalHeight, minPictureSize}
          ),
        ]);
        rejected = true;
      }
    }
    if (!rejected) {
      setCustomFileRejections(null);
      dispatch({type: 'START_EDITING', imageSrc});
    }
  };

  const dropzone = useDropzone({
    onDragEnter: markTouched,
    onFileDialogCancel: markTouched,
    onDrop: markTouched,
    onDropAccepted,
    disabled: disabled || (isUploading || failed || isCapturing || isEditing),
    accept: ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
    multiple: false,
    noClick: true,
    noKeyboard: true,
    maxSize: Indico.FileRestrictions.MaxUploadFileSize
      ? Indico.FileRestrictions.MaxUploadFileSize * 1024 * 1024
      : undefined,
  });

  let picture = null;
  if (!isInitialPicture && isEditing) {
    picture = {
      imageSrc: pictureState.imageSrc,
    };
  } else if (
    !isInitialPicture &&
    !isCapturing &&
    (pictureState.picture.uuid === null || pictureState.picture.uuid === value)
  ) {
    picture = {
      filename: pictureState.picture.filename,
      size: pictureState.picture.size,
      upload: {
        failed,
        ongoing: isUploading,
        finished: uploadFinished,
        progress: pictureState.progress,
      },
    };
  } else if (initialPictureDetails !== null && value === initialPictureDetails.uuid) {
    picture = initialPictureDetails;
  }

  let pictureAction = null;
  if (failed || uploadFinished) {
    pictureAction = {onClick: reset, icon: 'undo'};
  } else if (isInitialPicture && !required) {
    pictureAction = {onClick: clear, icon: 'x', color: 'red'};
  }

  useEffect(() => {
    if (!setValidationError) {
      return;
    }
    if (isUploading) {
      setValidationError(Translate.string('Upload in progress'));
    } else if (failed) {
      setValidationError(Translate.string('Picture upload/capture failed'));
    } else if (isCapturing) {
      setValidationError(Translate.string('Picture is being captured'));
    } else if (isEditing) {
      setValidationError(Translate.string('Picture is being edited'));
    } else {
      setValidationError(undefined);
    }
  }, [setValidationError, isUploading, failed, isCapturing, isEditing]);

  const capture = {
    pictureCamera: Camera,
    isCameraActive: isCapturing,
    isCameraAllowed,
    onOpenCameraDialog,
  };

  const cropper = {
    pictureCropper: Cropper,
    isEditActive: isEditing,
    onOpenEditDialog,
  };

  return (
    <PictureArea
      dropzone={dropzone}
      capture={capture}
      cropper={cropper}
      picture={picture}
      pictureAction={pictureAction}
      picturePreview={getPreview}
      customFileRejections={
        customFileRejections || errorMessages
          ? [...(customFileRejections || []), ...(errorMessages || [])]
          : null
      }
    />
  );
};
PictureManager.propTypes = {
  value: PropTypes.string,
  disabled: PropTypes.bool.isRequired,
  required: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  setValidationError: PropTypes.func,
  initialPictureDetails: fileDetailsShape,
  uploadURL: PropTypes.string.isRequired,
  previewURL: PropTypes.string.isRequired,
  minPictureSize: PropTypes.number,
};

PictureManager.defaultProps = {
  value: null,
  setValidationError: null,
  initialPictureDetails: null,
  minPictureSize: null,
};

export default function FinalPictureManager({name, ...rest}) {
  return (
    <Field
      name={`_${name}_invalidator`}
      validate={value => value || undefined}
      render={({input: {onChange: setDummyValue}}) => (
        <FinalField
          name={name}
          component={PictureManager}
          setValidationError={setDummyValue}
          {...rest}
        />
      )}
    />
  );
}

FinalPictureManager.propTypes = {
  name: PropTypes.string.isRequired,
  uploadURL: PropTypes.string.isRequired,
  previewURL: PropTypes.string.isRequired,
  initialPictureDetails: fileDetailsShape,
};

FinalPictureManager.defaultProps = {
  initialPictureDetails: null,
};
