// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventURL from 'indico-url:events.display';

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {List, Icon} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';
import '../ResultList.module.scss';

import CategoryPath from './CategoryPath';

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

const Event = ({typeFormat: type, eventId, title, categoryPath, startDt, endDt, chairPersons}) => {
  return (
    <div styleName="item">
      <List.Header styleName="header">
        <a href={eventURL({event_id: eventId})}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
        {/* if it's a lecture print the list of speakers */}
        {type === 'lecture' && chairPersons.length !== 0 && (
          <List.Item>
            {chairPersons.map(i => (
              <div key={i.name}>
                {i.title
                  ? `${i.title} ${i.name} (${i.affiliation})`
                  : `${i.name} (${i.affiliation})`}
              </div>
            ))}
          </List.Item>
        )}

        {renderDates(startDt, endDt)}
        {/* Render the path */}
        {categoryPath.length !== 0 && (
          <List.Item>
            <List.Description>
              <CategoryPath path={categoryPath} />
            </List.Description>
          </List.Item>
        )}
      </List.Description>
    </div>
  );
};

Event.defaultProps = {
  chairPersons: [],
  typeFormat: 'meeting',
};

const personShape = PropTypes.shape({
  id: PropTypes.number,
  name: PropTypes.string.isRequired,
  affiliation: PropTypes.string.isRequired,
});

Event.propTypes = {
  title: PropTypes.string.isRequired,
  eventId: PropTypes.number.isRequired,
  typeFormat: PropTypes.oneOf(['lecture', 'meeting', 'conference']),
  startDt: PropTypes.string.isRequired,
  endDt: PropTypes.string.isRequired,
  categoryPath: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
    })
  ).isRequired,
  chairPersons: PropTypes.arrayOf(personShape),
};

export default Event;
