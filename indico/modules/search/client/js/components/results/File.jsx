// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {List, Icon} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';

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

const File = ({title, url, typeFormat: type, filename, modifiedDt, user}) => (
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
    </List.Description>
  </div>
);

File.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  typeFormat: PropTypes.string.isRequired,
  filename: PropTypes.string,
  modifiedDt: PropTypes.string.isRequired,
  user: PropTypes.shape({
    name: PropTypes.string.isRequired,
    affiliation: PropTypes.string,
  }),
};

File.defaultProps = {
  filename: undefined,
  user: null,
};

export default File;
