// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import notScheduledURL from 'indico-url:timetable.not_scheduled';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon} from 'semantic-ui-react';

import {CollapsibleContainer} from 'indico/react/components';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {ContributionDetails} from './EntryDetails';
import * as selectors from './selectors';
import {entrySchema} from './util';

import './UnscheduledContributions.module.scss';

function UnscheduledContributionList({
  contribs,
  uses24HourFormat,
  dispatch,
  selected,
  setSelected,
}) {
  const sessions = useSelector(selectors.getSessions);

  const makeHandleSelect = id => e => {
    e.stopPropagation();
    setSelected(state => {
      const set = new Set([...state, id]);
      if (state.has(id)) {
        set.delete(id);
      }
      return set;
    });
  };

  const makeHandleDrag = id => () => {
    if (selected.has(id)) {
      dispatch(actions.dragUnscheduledContribs(selected));
      setSelected(new Set());
    } else {
      dispatch(actions.dragUnscheduledContribs(new Set([id])));
    }
  };

  return contribs.map(contrib => (
    <ContributionDetails
      key={contrib.id}
      entry={{...contrib, deleted: true}}
      title={contrib.title}
      uses24HourFormat={uses24HourFormat}
      dispatch={dispatch}
      onDragStart={makeHandleDrag(contrib.id)}
      onClick={makeHandleSelect(contrib.id)}
      selected={selected.has(contrib.id)}
      icon={selected.has(contrib.id) ? 'check square outline' : 'square outline'}
      draggable
    >
      <p>Session: {sessions.get(contrib.sessionId)?.title}</p>
      <p>Duration: TODO</p>
    </ContributionDetails>
  ));
}

UnscheduledContributionList.propTypes = {
  contribs: PropTypes.arrayOf(entrySchema).isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
  dispatch: PropTypes.func.isRequired,
  selected: PropTypes.instanceOf(Set).isRequired,
  setSelected: PropTypes.func.isRequired,
};

export default function UnscheduledContributions() {
  const dispatch = useDispatch();
  const {eventId} = useSelector(selectors.getStaticData);
  const contribs = useSelector(selectors.getUnscheduled);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const selectedEntry = useSelector(selectors.getSelectedEntry);
  const [selected, setSelected] = useState(new Set());
  const uses24HourFormat = true; // TODO fix this with localeUses24HourTime
  const {data, loading} = useIndicoAxios({
    url: notScheduledURL({event_id: eventId}),
    trigger: showUnscheduled,
  });
  console.debug(data, loading, contribs); //TODO

  // ensure that the dragged contrib is cleared when dropping outside the calendar
  useEffect(() => {
    const onDrop = e =>
      e.target.className !== 'rbc-events-container' &&
      dispatch(actions.dragUnscheduledContribs(new Set()));
    document.addEventListener('drop', onDrop);
    return () => {
      document.removeEventListener('drop', onDrop);
    };
  }, [dispatch]);

  // ensure that the selections are cleared when the list changes
  useEffect(() => {
    setSelected(new Set());
  }, [contribs]);

  if (!showUnscheduled) {
    return null;
  }

  const [currentContribs, otherContribs] = _.partition(
    contribs,
    c => c.sessionId === selectedEntry?.sessionId
  );

  return (
    <div styleName="contributions-container" onClick={() => setSelected(new Set())}>
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
        {currentContribs.length > 0 ? (
          <UnscheduledContributionList
            contribs={currentContribs}
            uses24HourFormat={uses24HourFormat}
            dispatch={dispatch}
            selected={selected}
            setSelected={setSelected}
          />
        ) : (
          <p>
            {selectedEntry?.sessionId ? (
              <Translate>
                There are no unscheduled contributions for the selected session.
              </Translate>
            ) : otherContribs.length > 0 ? (
              <Translate>
                There are no unscheduled contributions with no assigned session.
              </Translate>
            ) : (
              <Translate>There are no unscheduled contributions in this event.</Translate>
            )}
          </p>
        )}
        {otherContribs.length > 0 && (
          <CollapsibleContainer
            title={`${Translate.string('Contributions for other sessions')} (${
              otherContribs.length
            })`}
            titleSize="small"
          >
            <UnscheduledContributionList
              contribs={otherContribs}
              uses24HourFormat={uses24HourFormat}
              dispatch={dispatch}
              selected={selected}
              setSelected={setSelected}
            />
          </CollapsibleContainer>
        )}
      </div>
    </div>
  );
}
