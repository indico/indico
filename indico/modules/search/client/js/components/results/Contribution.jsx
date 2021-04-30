// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionURL from 'indico-url:contributions.display_contribution';
import subcontributionURL from 'indico-url:contributions.display_subcontribution';

import PropTypes from 'prop-types';
import React from 'react';
import {List, Icon} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';

import PersonList from './PersonList';

import '../ResultList.module.scss';

function Contribution({eventId, contributionId, subcontributionId, title, startDt, persons}) {
  const urlParams = {event_id: eventId, contrib_id: contributionId};
  const url = subcontributionId
    ? subcontributionURL({...urlParams, subcontrib_id: subcontributionId})
    : contributionURL(urlParams);

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
      </List.Description>
    </div>
  );
}

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  contributionId: PropTypes.number.isRequired,
  subcontributionId: PropTypes.number,
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
  subcontributionId: undefined,
};

export default Contribution;
