// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {ContributionDetails} from './EntryDetails';
import * as selectors from './selectors';

import './UnscheduledContributions.module.scss';

export default function UnscheduledContributions() {
  const dispatch = useDispatch();
  const contribs = useSelector(selectors.getUnscheduled);
  const uses24HourFormat = true; // TODO fix this with localeUses24HourTime

  if (contribs.length === 0) {
    return null;
  }

  return (
    <div styleName="contributions-container">
      <div styleName="content">
        <Translate as="h4">Unscheduled contributions</Translate>
        {contribs.map(contrib => (
          <ContributionDetails
            key={contrib.id}
            entry={{...contrib, deleted: true}}
            uses24HourFormat={uses24HourFormat}
            dispatch={dispatch}
            onDragStart={() => dispatch(actions.dragUnscheduledContrib(contrib.id))}
            draggable
            showTitle
          />
        ))}
      </div>
    </div>
  );
}
