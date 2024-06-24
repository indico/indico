// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {ContributionDetails} from './EntryDetails';
import * as selectors from './selectors';

import './UnscheduledContributions.module.scss';

export default function UnscheduledContributions() {
  const dispatch = useDispatch();
  const contribs = useSelector(selectors.getUnscheduled);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const uses24HourFormat = true; // TODO fix this with localeUses24HourTime

  // ensure that the dragged contrib is cleared when dropping outside the calendar
  useEffect(() => {
    const onDrop = e =>
      e.target.className !== 'rbc-events-container' &&
      dispatch(actions.dragUnscheduledContrib(null));
    document.addEventListener('drop', onDrop);
    return () => {
      document.removeEventListener('drop', onDrop);
    };
  }, [dispatch]);

  if (!showUnscheduled) {
    return null;
  }

  return (
    <div styleName="contributions-container">
      <div styleName="content">
        <h4>
          <Translate>Unscheduled contributions</Translate>
          <Icon
            name="close"
            color="black"
            onClick={() => dispatch(actions.toggleShowUnscheduled())}
            title={Translate.string('Hide unscheduled contributions')}
            link
          />
        </h4>
        {contribs.length > 0 ? (
          contribs.map(contrib => (
            <ContributionDetails
              key={contrib.id}
              entry={{...contrib, deleted: true}}
              uses24HourFormat={uses24HourFormat}
              dispatch={dispatch}
              onDragStart={() => dispatch(actions.dragUnscheduledContrib(contrib.id))}
              onDrop={(...args) => console.debug('onDrop', args)}
              draggable
              showTitle
            />
          ))
        ) : (
          <Translate as="p">
            There are currently no unscheduled contributions in this event.
          </Translate>
        )}
      </div>
    </div>
  );
}
