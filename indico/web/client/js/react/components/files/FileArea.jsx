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
  Icon,
  Progress,
  Message,
} from 'semantic-ui-react';

import {TooltipIfTruncated} from 'indico/react/components';
import {Translate, Param} from 'indico/react/i18n';

import {fileDetailsShape, dropzoneShape, fileActionShape} from './props';

import './FileArea.module.scss';

function humanReadableBytes(bytes) {
  const kiloBytes = 1000;
  const megaBytes = 1000 * kiloBytes;

  if (bytes < kiloBytes) {
    return (
      <Translate>
        <Param name="size" value={bytes} /> bytes
      </Translate>
    );
  } else if (bytes < megaBytes) {
    return (
      <Translate>
        <Param name="size" value={(bytes / kiloBytes).toFixed(2)} /> kB
      </Translate>
    );
  } else {
    return (
      <Translate>
        <Param name="size" value={(bytes / megaBytes).toFixed(2)} /> MB
      </Translate>
    );
  }
}

export function FileArea({
  dropzone: {getRootProps, getInputProps, isDragActive, open: openFileDialog},
  files,
  dragText,
  uploadButtonText,
  uploadButtonIcon,
  fileAction,
  errors,
}) {
  // unfortunately dropzone does not include the `disabled` flag, but the
  // `open` function is always null when the dropzone is disabled
  const dropzoneDisabled = openFileDialog === null;

  return (
    <div {...getRootProps()} styleName="dropzone-area">
      <input {...getInputProps()} />
      <Segment textAlign="center" placeholder>
        <Grid celled="internally">
          <Grid.Row columns={files.length === 0 ? 1 : 2}>
            {!isDragActive && files.length !== 0 && (
              <Grid.Column width={10} verticalAlign="middle">
                <Card.Group itemsPerRow={files.length === 1 ? 1 : 2} centered>
                  {files.map(file => (
                    <Card
                      styleName="file-card"
                      key={file.filename}
                      centered={files.length === 1}
                      raised
                    >
                      <Card.Content>
                        <Card.Header textAlign="center">
                          <TooltipIfTruncated>
                            <div styleName="filename">
                              {file.upload && !file.upload.finished && (
                                <Icon
                                  loading
                                  name={file.upload.failed ? 'exclamation' : 'spinner'}
                                />
                              )}
                              {file.filename}
                            </div>
                          </TooltipIfTruncated>
                        </Card.Header>
                        <Card.Meta textAlign="center">{humanReadableBytes(file.size)}</Card.Meta>
                        {file.upload && !file.upload.finished && (
                          <Progress
                            percent={file.upload.progress}
                            error={file.upload.failed}
                            size="tiny"
                            active
                            color="blue"
                          />
                        )}
                      </Card.Content>
                      {fileAction && (
                        <Icon
                          styleName="action"
                          name={fileAction.icon}
                          color={fileAction.color}
                          onClick={() => fileAction.onClick(file)}
                        />
                      )}
                    </Card>
                  ))}
                </Card.Group>
              </Grid.Column>
            )}
            <Grid.Column verticalAlign="middle" width={files.length === 0 || isDragActive ? 16 : 6}>
              <Header>{dragText}</Header>
              {!isDragActive && (
                <>
                  <Divider horizontal>
                    <Translate>Or</Translate>
                  </Divider>
                  <Button
                    type="button"
                    styleName="file-selection-btn"
                    icon={uploadButtonIcon}
                    content={uploadButtonText}
                    onClick={() => openFileDialog()}
                    disabled={dropzoneDisabled}
                  />
                </>
              )}
            </Grid.Column>
          </Grid.Row>
        </Grid>
        {errors && (
          <Message negative>
            <Message.Header>
              <Translate>There were some problems with your file</Translate>
            </Message.Header>
            <Message.List>
              {errors.map(err => (
                <Message.Item key={err}>{err}</Message.Item>
              ))}
            </Message.List>
          </Message>
        )}
      </Segment>
    </div>
  );
}

FileArea.propTypes = {
  dropzone: dropzoneShape.isRequired,
  files: PropTypes.arrayOf(fileDetailsShape).isRequired,
  dragText: PropTypes.string,
  uploadButtonText: PropTypes.string,
  uploadButtonIcon: PropTypes.string,
  fileAction: fileActionShape,
  errors: PropTypes.arrayOf(PropTypes.string),
};
FileArea.defaultProps = {
  dragText: Translate.string('Drag file(s) here'),
  uploadButtonText: Translate.string('Choose from your computer'),
  uploadButtonIcon: 'upload',
  fileAction: null,
  errors: null,
};

export function SingleFileArea({file, ...rest}) {
  const files = file ? [file] : [];
  const dragText = file
    ? Translate.string('Drag file here to replace')
    : Translate.string('Drag file here');
  const uploadButtonText = file
    ? Translate.string('Choose new file from your computer')
    : Translate.string('Choose from your computer');
  const uploadButtonIcon = file ? 'exchange' : 'upload';

  return (
    <FileArea
      files={files}
      dragText={dragText}
      uploadButtonIcon={uploadButtonIcon}
      uploadButtonText={uploadButtonText}
      {...rest}
    />
  );
}

SingleFileArea.propTypes = {
  dropzone: dropzoneShape.isRequired,
  file: fileDetailsShape,
  fileAction: fileActionShape,
  errors: PropTypes.arrayOf(PropTypes.string),
};

SingleFileArea.defaultProps = {
  file: null,
  fileAction: null,
  errors: null,
};
