// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {List, Icon} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';

import {Path, pathPropType} from './Path';
import PersonList from './PersonList';

import '../ResultList.module.scss';

const iconSelector = filename => {
  switch (filename?.split('.').pop()) {
    case 'doc':
    case 'docx':
      return {color: 'blue', name: 'file word outline'};
    case 'md':
    case 'txt':
      return {color: 'blue', name: 'file alternate outline'};
    case 'zip':
      return {color: 'yellow', name: 'file archive outline'};
    case 'ppt':
    case 'pptx':
    case 'key':
      return {color: 'red', name: 'file powerpoint outline'};
    case 'xls':
    case 'xlsx':
      return {color: 'green', name: 'file excel outline'};
    case 'pdf':
      return {color: 'red', name: 'file pdf outline'};
    default:
      return {name: 'file outline'};
  }
};

export default function Attachment({
  title,
  url,
  attachmentType: type,
  filename,
  modifiedDt,
  user,
  categoryPath,
  eventPath,
  showCategoryPath,
}) {
  const path = showCategoryPath ? [...categoryPath, ...eventPath] : eventPath;
  return (
    <div styleName="item">
      <List.Header styleName="header">
        <Icon size="large" {...(type === 'file' ? iconSelector(filename) : {name: 'linkify'})} />
        <a href={url}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
        {user && (
          <List.Item>
            <PersonList persons={[user]} />
          </List.Item>
        )}
        <List.Item>
          <Icon name="calendar alternate outline" />
          {serializeDate(toMoment(modifiedDt), 'DD MMMM YYYY HH:mm')}
        </List.Item>
        {path.length !== 0 && (
          <List.Item>
            <List.Description>
              <Path path={path} />
            </List.Description>
          </List.Item>
        )}
      </List.Description>
    </div>
  );
}

Attachment.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  attachmentType: PropTypes.oneOf(['file', 'link']).isRequired,
  filename: PropTypes.string,
  modifiedDt: PropTypes.string.isRequired,
  user: PropTypes.shape({
    name: PropTypes.string.isRequired,
    affiliation: PropTypes.string,
  }),
  categoryPath: pathPropType.isRequired,
  eventPath: pathPropType.isRequired,
  showCategoryPath: PropTypes.bool.isRequired,
};

Attachment.defaultProps = {
  filename: undefined,
  user: null,
};
