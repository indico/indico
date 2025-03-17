// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {
  Button,
  Card,
  Divider,
  Grid,
  Header,
  Segment,
  Image,
  Icon,
  Popup,
  Progress,
  Message,
} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {dropzoneShape, fileActionShape} from '../files/props';

import './Picture.module.scss';

export function PictureArea({
  dropzone: {getRootProps, getInputProps, isDragActive, open: openUploadDialog, fileRejections},
  capture: {pictureCamera: PictureCamera, onOpenCameraDialog, isCameraActive, isCameraAllowed},
  cropper: {pictureCropper: PictureCropper, onOpenEditDialog, isEditActive},
  picture,
  dragText,
  pictureAction,
  picturePreview,
  customFileRejections,
}) {
  const uploadButtonIcon = picture ? 'exchange' : 'upload';
  const uploadButtonText = picture
    ? Translate.string('Choose a new picture from your computer')
    : Translate.string('Choose from your computer');
  const captureButtonIcon = 'camera';
  const captureButtonText = picture
    ? Translate.string('Take a new picture')
    : Translate.string('Take a picture');
  const dropzoneDisabled = openUploadDialog === null;

  return (
    <div {...getRootProps()} styleName="dropzone-area">
      <input {...getInputProps()} />
      <Segment textAlign="center" placeholder>
        {picture && picture.imageSrc && isEditActive && <PictureCropper />}
        {isCameraActive && <PictureCamera />}
        {!isEditActive && !isCameraActive && (
          <Grid celled="internally">
            <Grid.Row columns={picture ? 2 : 1}>
              {!isDragActive && picture && (
                <Grid.Column width={10} verticalAlign="middle">
                  <Card styleName="picture-card" key={picture.filename} centered>
                    {/* XXX: Container and class to be used by plugins */}
                    <div className="picture-preview-container">
                      <Image src={picturePreview()} size="large" rounded />
                    </div>
                    {picture.upload && !picture.upload.finished && (
                      <Progress
                        percent={picture.upload.progress}
                        error={picture.upload.failed}
                        size="tiny"
                        active
                        color="blue"
                      />
                    )}
                    {pictureAction && (
                      <Icon
                        bordered
                        styleName="action"
                        name={pictureAction.icon}
                        color={pictureAction.color}
                        onClick={() => pictureAction.onClick(picture)}
                      />
                    )}
                  </Card>
                </Grid.Column>
              )}
              <Grid.Column verticalAlign="middle" width={!isDragActive && picture ? 6 : 16}>
                <Header>
                  {!isDragActive ? dragText : <Translate>Drop picture here</Translate>}
                </Header>
                {!isDragActive && (
                  <>
                    <Divider horizontal>
                      <Translate>Or</Translate>
                    </Divider>
                    {picture ? (
                      <>
                        <Button
                          type="button"
                          styleName="picture-selection-btn"
                          icon={uploadButtonIcon}
                          content={uploadButtonText}
                          onClick={() => openUploadDialog()}
                          disabled={dropzoneDisabled}
                        />
                        <Divider horizontal>
                          <Translate>Or</Translate>
                        </Divider>
                        <Popup
                          position="top center"
                          trigger={
                            <span>
                              <Button
                                type="button"
                                styleName="picture-selection-btn"
                                icon={captureButtonIcon}
                                content={captureButtonText}
                                onClick={() => onOpenCameraDialog()}
                                disabled={!isCameraAllowed}
                              />
                            </span>
                          }
                          content={
                            isCameraAllowed
                              ? Translate.string('Take a picture with your camera')
                              : Translate.string(
                                  'You need to grant this site camera permissions before taking a picture'
                                )
                          }
                        />
                        <Divider horizontal>
                          <Translate>Or</Translate>
                        </Divider>
                        <Button
                          type="button"
                          styleName="picture-selection-btn"
                          icon="edit"
                          content={Translate.string('Edit current picture')}
                          onClick={() => onOpenEditDialog()}
                        />
                      </>
                    ) : (
                      <Grid columns={2} verticalAlign="middle" celled="internally">
                        <Grid.Column>
                          <Button
                            type="button"
                            styleName="picture-selection-btn"
                            icon={uploadButtonIcon}
                            content={uploadButtonText}
                            onClick={() => openUploadDialog()}
                            disabled={dropzoneDisabled}
                          />
                        </Grid.Column>
                        <Grid.Column>
                          <Popup
                            position="top center"
                            trigger={
                              <span>
                                <Button
                                  type="button"
                                  styleName="picture-selection-btn last-picture-selection-btn"
                                  icon={captureButtonIcon}
                                  content={captureButtonText}
                                  onClick={() => onOpenCameraDialog()}
                                  disabled={!isCameraAllowed}
                                />
                              </span>
                            }
                            content={
                              isCameraAllowed
                                ? Translate.string('Take a picture with your camera')
                                : Translate.string(
                                    'You need to grant this site camera permissions before taking a picture'
                                  )
                            }
                          />
                        </Grid.Column>
                      </Grid>
                    )}
                  </>
                )}
                <Divider horizontal />
              </Grid.Column>
            </Grid.Row>
          </Grid>
        )}
        {(fileRejections.length > 0 || customFileRejections) && (
          <Message negative>
            <Message.Header>
              <Translate>There were some problems with the picture</Translate>
            </Message.Header>
            {fileRejections.map(({file, errors}) => (
              <Message.List key={file.path}>
                {errors.map(e => (
                  <Message.Item key={e.code}>
                    {file.name}: {e.message}
                  </Message.Item>
                ))}
              </Message.List>
            ))}
            {customFileRejections && (
              <Message.List>
                {customFileRejections.map(err => (
                  <Message.Item key={err}>{err}</Message.Item>
                ))}
              </Message.List>
            )}
          </Message>
        )}
      </Segment>
    </div>
  );
}

const pictureDetailsShape = PropTypes.shape({
  filename: PropTypes.string,
  size: PropTypes.number,
  uuid: PropTypes.string,
  imageSrc: PropTypes.string,
  upload: PropTypes.shape({
    failed: PropTypes.bool.isRequired,
    ongoing: PropTypes.bool.isRequired,
    finished: PropTypes.bool.isRequired,
    progress: PropTypes.number.isRequired,
  }),
});

PictureArea.propTypes = {
  dropzone: dropzoneShape.isRequired,
  capture: PropTypes.object.isRequired,
  cropper: PropTypes.object.isRequired,
  picture: pictureDetailsShape,
  dragText: PropTypes.string,
  pictureAction: fileActionShape,
  picturePreview: PropTypes.func.isRequired,
  customFileRejections: PropTypes.arrayOf(PropTypes.string),
};

PictureArea.defaultProps = {
  picture: null,
  dragText: Translate.string('Drag a picture here'),
  pictureAction: null,
  customFileRejections: null,
};
