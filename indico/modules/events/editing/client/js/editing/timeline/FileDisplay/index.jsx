// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Button, Icon, Label} from 'semantic-ui-react';
import {TooltipIfTruncated} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {fileTypePropTypes, filePropTypes, mapFileTypes} from '../FileManager/util';
import './FileDisplay.module.scss';

function FileListDisplay({files}) {
  return (
    <ul styleName="file-list-display">
      {files.map(({filename, uuid, downloadURL}) => (
        <li key={uuid} styleName="file-row">
          <TooltipIfTruncated>
            <span styleName="file-name">
              <a href={downloadURL} target="_blank" rel="noopener noreferrer">
                {filename}
              </a>
            </span>
          </TooltipIfTruncated>
        </li>
      ))}
      {!files.length && (
        <span styleName="no-files">
          <Translate>No files uploaded</Translate>
        </span>
      )}
    </ul>
  );
}

FileListDisplay.propTypes = {
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
};

function FileTypeDisplay({fileType}) {
  return (
    <div styleName="file-type-display">
      <h3>{fileType.name}</h3>
      <FileListDisplay files={fileType.files} />
    </div>
  );
}

FileTypeDisplay.propTypes = {
  fileType: PropTypes.shape(fileTypePropTypes).isRequired,
};

export default function FileDisplay({downloadURL, fileTypes, files, tags}) {
  return (
    <div styleName="file-display-wrapper">
      <div styleName="file-display">
        {mapFileTypes(fileTypes, files).map(fileType => (
          <FileTypeDisplay key={fileType.id} fileType={fileType} />
        ))}
      </div>
      <div styleName="download-tag-wrapper">
        <div styleName="tag-display">
          {tags.map(tag => (
            <Label color={tag.color} key={tag.id}>
              {tag.verboseTitle}
            </Label>
          ))}
        </div>
        {files.length !== 0 && (
          <div>
            <Button
              as="a"
              href={downloadURL}
              floated="right"
              styleName="download-button"
              icon
              primary
            >
              <Icon name="download" /> <Translate>Download ZIP</Translate>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

FileDisplay.propTypes = {
  downloadURL: PropTypes.string.isRequired,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
  tags: PropTypes.arrayOf(
    PropTypes.shape({
      color: PropTypes.string.isRequired,
      id: PropTypes.number.isRequired,
      verboseTitle: PropTypes.string.isRequired,
    })
  ).isRequired,
};
