// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Label, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {toClasses} from 'indico/react/util';

import './OccurrencesCounter.module.scss';

export default function OccurrencesCounter({bookingsCount, newBookingsCount, pastBookingsCount}) {
  return (
    <div styleName="occurrence-count">
      <Popup
        trigger={<Label color="blue" size="tiny" content={bookingsCount} circular />}
        position="bottom center"
        on="hover"
      >
        <Translate>Number of booking occurrences</Translate>
      </Popup>
      {newBookingsCount !== null && (
        <div>
          {pastBookingsCount !== null && (
            <div styleName="old-occurrences-count">
              <div styleName="arrow">→</div>
              <Popup
                trigger={<Label size="tiny" content={pastBookingsCount} color="orange" circular />}
                position="bottom center"
                on="hover"
              >
                <Translate>Number of past occurrences that will not be modified</Translate>
              </Popup>
            </div>
          )}
          <div
            className={toClasses({
              'new-occurrences-count': true,
              'single-arrow': pastBookingsCount === null,
            })}
          >
            <div styleName="arrow">→</div>
            <Popup
              trigger={<Label size="tiny" content={newBookingsCount} color="green" circular />}
              position="bottom center"
              on="hover"
            >
              <Translate>Number of new occurrences after changes</Translate>
            </Popup>
          </div>
        </div>
      )}
    </div>
  );
}

OccurrencesCounter.propTypes = {
  bookingsCount: PropTypes.number.isRequired,
  newBookingsCount: PropTypes.number,
  pastBookingsCount: PropTypes.number,
};

OccurrencesCounter.defaultProps = {
  newBookingsCount: null,
  pastBookingsCount: null,
};
