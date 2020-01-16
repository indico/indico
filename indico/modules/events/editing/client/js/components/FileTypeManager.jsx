// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';

import React from 'react';
import PropTypes from 'prop-types';
import {Button, Icon, Loader, Message, Segment} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {useIndicoAxios} from 'indico/react/hooks';

import './FileTypeManager.module.scss';

export default function FileTypeManager({eventId}) {
  const {data, loading: isLoadingFileTypes, lastData} = useIndicoAxios({
    url: fileTypesURL({confId: eventId}),
    camelize: true,
    trigger: eventId,
  });

  const fileTypes = data || lastData;
  if (isLoadingFileTypes && !lastData) {
    return <Loader inline="centered" active />;
  } else if (!fileTypes) {
    return null;
  }

  return (
    <div styleName="file-types-container">
      {fileTypes.length === 0 && (
        <Message info>
          <Translate>There are no file types defined for this event</Translate>
        </Message>
      )}
      {fileTypes.map(fileType => (
        <Segment key={fileType.id} styleName="filetype-segment">
          <div styleName="filetype">
            <div>
              <h3>{fileType.name}</h3>
              <ul styleName="file-extensions">
                {fileType.extensions.length !== 0
                  ? fileType.extensions.map(ext => <li key={ext}>{ext}</li>)
                  : Translate.string('(no extension restrictions)')}
              </ul>
            </div>
            <div styleName="actions">
              <Icon color="blue" name="pencil" />
              <Icon color="red" name="trash" />
            </div>
          </div>
        </Segment>
      ))}
      <Button icon primary floated="right">
        <Icon name="plus" />
        <Translate>Add a new file type</Translate>
      </Button>
    </div>
  );
}

FileTypeManager.propTypes = {
  eventId: PropTypes.number.isRequired,
};
