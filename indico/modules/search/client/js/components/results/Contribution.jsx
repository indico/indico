// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {List, Icon} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import {toMoment, serializeDate} from 'indico/utils/date';

import './Contribution.module.scss';

const Contribution = ({title, url, startDt, eventURL, eventTitle, persons}) => (
  <div styleName="contribution">
    <List.Header>
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      <List.Item styleName="high-priority">
        {/* change to something that reminds an event */}
        <Icon name="calendar check outline" />
        <a href={eventURL}>{eventTitle}</a>
      </List.Item>
      <List.Item>
        {persons.length !== 0 && (
          <ul styleName="high-priority">
            {persons.length > 1 ? <Icon name="users" /> : <Icon name="user" />}
            {persons.map(person => (
              <li key={person.id}>
                {person.title ? `${person.title} ${person.name}` : person.name}
              </li>
            ))}
          </ul>
        )}
      </List.Item>
      <List.Item styleName="med-priority">
        <Icon name="calendar alternate outline" />
        {serializeDate(toMoment(startDt), 'DD MMMM YYYY HH:mm')}
      </List.Item>
    </List.Description>
  </div>
);

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  startDt: PropTypes.string.isRequired,
  eventURL: PropTypes.string.isRequired,
  eventTitle: PropTypes.string.isRequired,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,
};
export default Contribution;
