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

import {Path, pathPropType} from './Path';
import PersonList from './PersonList';

import '../ResultList.module.scss';

export default function Contribution({url, title, startDt, persons, categoryPath, eventPath}) {
  return (
    <div styleName="item">
      <List.Header styleName="header">
        <a href={url}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
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
        {categoryPath.length !== 0 && (
          <List.Item>
            <List.Description>
              <Path path={[...categoryPath, ...eventPath]} />
            </List.Description>
          </List.Item>
        )}
      </List.Description>
    </div>
  );
}

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  startDt: PropTypes.string,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      affiliation: PropTypes.string,
    })
  ),
  categoryPath: pathPropType.isRequired,
  eventPath: pathPropType.isRequired,
};

Contribution.defaultProps = {
  startDt: null,
  persons: [],
};
