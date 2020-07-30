// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Button, Card, Divider, Grid, Header, Segment, Icon} from 'semantic-ui-react';
import {TooltipIfTruncated} from 'indico/react/components';
import {Translate, Param} from 'indico/react/i18n';

import './FileArea.module.scss';
import {fileDetailsShape} from './props';

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
  dropzoneRootProps,
  dropzoneInputProps,
  hideFiles,
  files,
  disabled,
  onChooseFileClick,
  dragText,
  fileAction,
}) {
  return (
    <div {...dropzoneRootProps} styleName="dropzone-area">
      <input {...dropzoneInputProps} />
      <Segment textAlign="center" placeholder>
        <Grid celled="internally">
          <Grid.Row columns={files.length === 0 ? 1 : 2}>
            {!hideFiles && files.length !== 0 && (
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
                            <div style={{textOverflow: 'ellipsis', overflow: 'hidden'}}>
                              {file.filename}
                            </div>
                          </TooltipIfTruncated>
                        </Card.Header>
                        <Card.Meta textAlign="center">{humanReadableBytes(file.size)}</Card.Meta>
                      </Card.Content>
                      {!disabled && fileAction && (
                        <Icon
                          name={fileAction.icon}
                          color={fileAction.color}
                          style={{cursor: 'pointer'}}
                          onClick={() => fileAction.onClick(file)}
                        />
                      )}
                    </Card>
                  ))}
                </Card.Group>
              </Grid.Column>
            )}
            <Grid.Column verticalAlign="middle" width={files.length === 0 || hideFiles ? 16 : 6}>
              <Header>{dragText}</Header>
              {!hideFiles && (
                <>
                  <Divider horizontal>
                    <Translate>Or</Translate>
                  </Divider>
                  <Button
                    type="button"
                    styleName="file-selection-btn"
                    icon="upload"
                    content={Translate.string('Choose from your computer')}
                    onClick={() => onChooseFileClick()}
                    disabled={disabled}
                  />
                </>
              )}
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </Segment>
    </div>
  );
}

FileArea.propTypes = {
  dropzoneRootProps: PropTypes.object.isRequired,
  dropzoneInputProps: PropTypes.object.isRequired,
  hideFiles: PropTypes.bool.isRequired,
  files: PropTypes.arrayOf(fileDetailsShape).isRequired,
  disabled: PropTypes.bool.isRequired,
  onChooseFileClick: PropTypes.func.isRequired,
  dragText: PropTypes.string,
  fileAction: PropTypes.shape({
    icon: PropTypes.string.isRequired,
    color: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired,
  }),
};
FileArea.defaultProps = {
  dragText: Translate.string('Drag file(s) here'),
  fileAction: null,
};

export function SingleFileArea({hideFile, file, ...rest}) {
  return (
    <FileArea
      hideFiles={hideFile}
      files={file ? [file] : []}
      dragText={Translate.string('Drag file here')}
      {...rest}
    />
  );
}

SingleFileArea.propTypes = {
  dropzoneRootProps: PropTypes.object.isRequired,
  dropzoneInputProps: PropTypes.object.isRequired,
  hideFile: PropTypes.bool.isRequired,
  file: fileDetailsShape,
  disabled: PropTypes.bool.isRequired,
  onChooseFileClick: PropTypes.func.isRequired,
  fileAction: PropTypes.shape({
    icon: PropTypes.string.isRequired,
    color: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired,
  }),
};

SingleFileArea.defaultProps = {
  file: null,
  fileAction: null,
};
