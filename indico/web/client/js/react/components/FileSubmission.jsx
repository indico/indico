// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useCallback, useRef, useState} from 'react';
import PropTypes from 'prop-types';
import Dropzone from 'react-dropzone';
import {Button, Card, Divider, Grid, Header, Icon, Segment} from 'semantic-ui-react';

import {TooltipIfTruncated} from 'indico/react/components';
import {Param, Translate} from 'indico/react/i18n';

import './FileSubmission.module.scss';

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

export default function FileSubmission({onChange, disabled}) {
  const [files, setFiles] = useState([]);
  const onDrop = useCallback(
    acceptedFiles => {
      const newFilenames = new Set(acceptedFiles.map(f => f.name));
      acceptedFiles = files.filter(f => !newFilenames.has(f.name)).concat(acceptedFiles);
      setFiles(acceptedFiles);
      if (onChange) {
        onChange(acceptedFiles);
      }
    },
    [files, setFiles, onChange]
  );

  const removeFile = file => {
    const newFiles = files.filter(f => f !== file);
    setFiles(newFiles);
    if (onChange) {
      onChange(newFiles);
    }
  };

  const dropzoneRef = useRef();
  const openFileDialog = () => {
    if (dropzoneRef.current && !disabled) {
      dropzoneRef.current.open();
    }
  };

  return (
    <Dropzone ref={dropzoneRef} onDrop={onDrop} disabled={disabled} multiple noClick noKeyboard>
      {({getRootProps, getInputProps, isDragActive}) => (
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
                          key={file.name}
                          centered={files.length === 1}
                          raised
                        >
                          {!disabled && (
                            <Icon name="trash" onClick={() => removeFile(file)} color="red" />
                          )}
                          <Card.Content>
                            <TooltipIfTruncated>
                              <Card.Header textAlign="center">{file.name}</Card.Header>
                            </TooltipIfTruncated>
                            <Card.Meta textAlign="center">
                              {humanReadableBytes(file.size)}
                            </Card.Meta>
                          </Card.Content>
                        </Card>
                      ))}
                    </Card.Group>
                  </Grid.Column>
                )}
                <Grid.Column
                  verticalAlign="middle"
                  width={files.length === 0 || isDragActive ? 16 : 6}
                >
                  <Header>
                    <Translate>Drag file(s) here</Translate>
                  </Header>
                  {!isDragActive && (
                    <>
                      <Divider horizontal>
                        <Translate>Or</Translate>
                      </Divider>
                      <Button
                        styleName="file-selection-btn"
                        icon="upload"
                        content={Translate.string('Choose from your computer')}
                        onClick={openFileDialog}
                        disabled={disabled}
                      />
                    </>
                  )}
                </Grid.Column>
              </Grid.Row>
            </Grid>
          </Segment>
        </div>
      )}
    </Dropzone>
  );
}

FileSubmission.propTypes = {
  onChange: PropTypes.func,
  disabled: PropTypes.bool,
};

FileSubmission.defaultProps = {
  onChange: null,
  disabled: false,
};
