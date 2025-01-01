// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {List, Icon} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';

import Highlight from './Highlight';
import {LocationItem, locationPropType} from './LocationItem';
import {Path, pathPropType} from './Path';
import PersonList from './PersonList';

import '../ResultList.module.scss';

/* if end date == start date only show start date */
const renderDates = (startDt, endDt) =>
  moment(startDt).isSame(moment(endDt), 'day') ? (
    <List.Item>
      <Icon name="calendar alternate outline" />
      {serializeDate(toMoment(startDt), 'DD MMMM YYYY HH:mm')}
    </List.Item>
  ) : (
    <List.Item>
      <Icon name="calendar alternate outline" />
      {`${serializeDate(toMoment(startDt), 'DD MMMM YYYY')} -
         ${serializeDate(toMoment(endDt), 'DD MMMM YYYY')}`}
    </List.Item>
  );

export default function Event({
  eventType,
  url,
  title,
  description,
  highlight,
  categoryPath,
  startDt,
  endDt,
  persons,
  location,
}) {
  return (
    <div styleName="item">
      <List.Header styleName="header">
        <a href={url}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
        <Highlight text={description} highlight={highlight.description} />
        {['lecture', 'meeting'].includes(eventType) && persons.length !== 0 && (
          <List.Item>
            <PersonList persons={persons} />
          </List.Item>
        )}
        {renderDates(startDt, endDt)}
        <LocationItem location={location} />
        {categoryPath.length !== 0 && (
          <List.Item>
            <List.Description>
              <Path path={categoryPath} />
            </List.Description>
          </List.Item>
        )}
      </List.Description>
    </div>
  );
}

Event.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  eventType: PropTypes.oneOf(['lecture', 'meeting', 'conference']).isRequired,
  startDt: PropTypes.string.isRequired,
  endDt: PropTypes.string.isRequired,
  categoryPath: pathPropType.isRequired,
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
};
