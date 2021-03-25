// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {List, Icon} from 'semantic-ui-react';

import './File.module.scss';
import {toMoment, serializeDate} from 'indico/utils/date';

const iconSelector = type => {
  const otherAttributes = {size: 'large'};
  switch (type) {
    case 'file-word':
      return {color: 'blue', name: 'file word outline', ...otherAttributes};
    case 'file-zip':
      return {color: 'yellow', name: 'file archive outline', ...otherAttributes};
    case 'file-presentation':
      return {color: 'red', name: 'file powerpoint outline', ...otherAttributes};
    case 'file-excel':
      return {color: 'green', name: 'file excel outline', ...otherAttributes};
    case 'file-pdf':
      return {color: 'red', name: 'file pdf outline', ...otherAttributes};
    case 'file-spreadsheet':
      return {color: 'green', name: 'file excel outline', ...otherAttributes};
    default:
      return {name: 'file outline', ...otherAttributes};
  }
};

const File = ({title, url, type, /* contributionTitle, contribURL,*/ modifiedDt, user}) => (
  <div styleName="file">
    <List.Header>
      <Icon {...iconSelector(type)} />
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      {/* <List.Item styleName="high-priority">*/}
      {/*  <Icon rotated="clockwise" name="level up alternate" />*/}
      {/*  <a href={contribURL}>{contributionTitle}</a>*/}
      {/* </List.Item>*/}
      <List.Item>
        <ul styleName="high-priority">
          <Icon name="user" />
          <li key={user.id}>{user.name}</li>
        </ul>
      </List.Item>
      <List.Item styleName="med-priority">
        <Icon name="calendar alternate outline" />
        {serializeDate(toMoment(modifiedDt), 'DD MMMM YYYY HH:mm')}
      </List.Item>
    </List.Description>
  </div>
);

File.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  // contributionTitle: PropTypes.string,
  modifiedDt: PropTypes.string.isRequired,
  // contribURL: PropTypes.string,
  user: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
  }).isRequired,
};
export default File;
