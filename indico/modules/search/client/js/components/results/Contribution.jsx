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

import Highlight from './Highlight';
import {LocationItem, locationPropType} from './LocationItem';
import {Path, pathPropType} from './Path';
import PersonList from './PersonList';

import '../ResultList.module.scss';

export default function Contribution({
  url,
  title,
  description,
  highlight,
  startDt,
  persons,
  categoryPath,
  eventPath,
  location,
  showCategoryPath,
}) {
  const path = showCategoryPath ? [...categoryPath, ...eventPath] : eventPath;
  return (
    <div styleName="item">
      <List.Header styleName="header">
        <a href={url}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
        <Highlight text={description} highlight={highlight.description} />
        {persons.length !== 0 && (
          <List.Item>
            <PersonList persons={persons} />
          </List.Item>
        )}
        {startDt && (
          <List.Item>
            <Icon name="calendar alternate outline" />
            {serializeDate(toMoment(startDt), 'DD MMMM YYYY HH:mm')}
          </List.Item>
        )}
        <LocationItem location={location} />
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

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  startDt: PropTypes.string,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      affiliation: PropTypes.string,
    })
  ).isRequired,
  location: locationPropType.isRequired,
  highlight: PropTypes.shape({
    description: PropTypes.array,
  }).isRequired,
  categoryPath: pathPropType.isRequired,
  eventPath: pathPropType.isRequired,
  showCategoryPath: PropTypes.bool.isRequired,
};

Contribution.defaultProps = {
  startDt: null,
};
