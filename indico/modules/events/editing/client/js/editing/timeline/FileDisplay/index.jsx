// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Button, Icon, Label, Message, Popup} from 'semantic-ui-react';

import {TooltipIfTruncated} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {toClasses} from 'indico/react/util';

import {fileTypePropTypes, filePropTypes, mapFileTypes} from '../FileManager/util';
import * as selectors from '../selectors';

import './FileDisplay.module.scss';

function FileListDisplay({files}) {
  const stateIcon = {
    modified: {
      icon: 'dot circle',
      color: 'yellow',
      tooltip: Translate.string('This file was modified since the last revision.'),
    },
    added: {
      icon: 'add circle',
      color: 'green',
      tooltip: Translate.string('This file was added since the last revision.'),
    },
  };

  return (
    <ul styleName="file-list-display">
      {files.map(({filename, uuid, downloadURL, state}) => (
        <li key={uuid} styleName="file-row">
          <TooltipIfTruncated>
            <span styleName="file-name">
              {state && (
                <Popup
                  trigger={<Icon name={stateIcon[state].icon} color={stateIcon[state].color} />}
                  content={stateIcon[state].tooltip}
                />
              )}
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

export default function FileDisplay({downloadURL, fileTypes, files, tags, outdated}) {
  const {canAssignSelf} = useSelector(selectors.getDetails);
  const canPerformSubmitterActions = useSelector(selectors.canPerformSubmitterActions);
  return (
    <div
      styleName={toClasses({
        'file-display-wrapper': true,
        outdated: outdated && files.length > 0,
      })}
    >
      {files.length !== 0 && (
        <div styleName="file-display">
          {mapFileTypes(fileTypes, files).map(fileType => (
            <FileTypeDisplay key={fileType.id} fileType={fileType} />
          ))}
        </div>
      )}
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
            {canAssignSelf && !canPerformSubmitterActions ? (
              <Popup
                trigger={
                  <Button floated="right" styleName="download-button" icon primary>
                    <Icon name="download" /> <Translate>Download ZIP</Translate>
                  </Button>
                }
                on="click"
                position="right center"
              >
                <div styleName="download-popup">
                  <Message warning>
                    <Icon name="warning sign" />
                    <Translate>
                      You haven't assigned this editable to yourself. Are you sure you want to
                      download it anyway?
                    </Translate>
                  </Message>
                  <Button
                    as="a"
                    href={downloadURL}
                    icon
                    styleName="confirm-download"
                    labelPosition="left"
                  >
                    <Icon name="download" />
                    <Translate>Download anyway</Translate>
                  </Button>
                </div>
              </Popup>
            ) : (
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
            )}
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
  outdated: PropTypes.bool,
};

FileDisplay.defaultProps = {
  outdated: false,
};
