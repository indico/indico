// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {List, Icon} from 'semantic-ui-react';
import PropTypes from 'prop-types';
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

const File = ({title, url, type, contributionTitle, date, contribURL, persons}) => (
  <div styleName="file">
    <List.Header>
      <Icon {...iconSelector(type)} />
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      <List.Item styleName="high-priority">
        <Icon rotated="clockwise" name="level up alternate" />
        <a href={contribURL}>{contributionTitle}</a>
      </List.Item>
      <List.Item>
        {persons.length !== 0 && (
          <ul styleName="high-priority">
            {persons.length > 1 ? <Icon name="users" /> : <Icon name="user" />}
            {persons.map(item => (
              <li key={item.id}>{item.title ? `${item.title} ${item.name}` : `${item.name}`}</li>
            ))}
          </ul>
        )}
      </List.Item>
      <List.Item styleName="med-priority">
        <Icon name="calendar alternate outline" />
        {serializeDate(toMoment(date), 'DD MMMM YYYY HH:mm')}
      </List.Item>
    </List.Description>
  </div>
);

File.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  contributionTitle: PropTypes.string.isRequired,
  date: PropTypes.string.isRequired,
  contribURL: PropTypes.string.isRequired,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,
};
export default File;
