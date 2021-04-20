// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionURL from 'indico-url:contributions.display_contribution';

import PropTypes from 'prop-types';
import React from 'react';
import {List, Icon} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';

import '../ResultList.module.scss';

const Contribution = ({eventId, contributionId, title, startDt, persons}) => {
  persons = [...new Map(persons.map(p => [p.name + p.affiliation, p])).values()];

  return (
    <div styleName="item">
      <List.Header styleName="header">
        <a href={contributionURL({event_id: eventId, contrib_id: contributionId})}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
        <List.Item>
          {persons.length !== 0 && (
            <ul>
              {persons.length > 1 ? <Icon name="users" /> : <Icon name="user" />}
              {persons.map(person => (
                <li key={person}>
                  {person.name}
                  <span styleName="muted">
                    {person.affiliation ? ` (${person.affiliation})` : ''}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </List.Item>
        {startDt && (
          <List.Item>
            <Icon name="calendar alternate outline" />
            {serializeDate(toMoment(startDt), 'DD MMMM YYYY HH:mm')}
          </List.Item>
        )}
      </List.Description>
    </div>
  );
};

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  contributionId: PropTypes.number.isRequired,
  eventId: PropTypes.number.isRequired,
  startDt: PropTypes.string,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      affiliation: PropTypes.string,
    })
  ),
};

Contribution.defaultProps = {
  startDt: undefined,
  persons: [],
};

export default Contribution;
