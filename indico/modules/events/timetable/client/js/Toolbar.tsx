// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {DRAFT_ENTRY_MODAL, useModal} from './ModalContext';
import * as selectors from './selectors';
import {getDiffInDays} from './utils';

import './Toolbar.module.scss';

export default function Toolbar() {
  const dispatch = useDispatch();
  const {openModal} = useModal();

  const ref = useRef(null);
  const eventId = useSelector(selectors.getEventId);
  const eventStart = useSelector(selectors.getEventStartDt);
  const eventEnd = useSelector(selectors.getEventEndDt);
  const numDays = useSelector(selectors.getEventNumDays);
  const isExpanded = useSelector(selectors.getIsExpanded);
  const currentDate = useSelector(selectors.getCurrentDate);
  const currentEntries = useSelector(selectors.getCurrentEntries);
  const expandedSessionBlock = useSelector(selectors.getExpandedSessionBlock);
  const defaultContributionDuration = useSelector(selectors.getDefaultContribDurationMinutes);
  const eventLocationParent = useSelector(selectors.getEventLocationParent);
  const currentDayIdx = getDiffInDays(eventStart, currentDate);
  const reachedLastDay = currentDayIdx >= numDays - 1;

  const addNewEntry = () => {
    let minDt, maxDt;

    if (expandedSessionBlock) {
      // Adding entry inside a session block
      minDt = moment(expandedSessionBlock.startDt);
      maxDt = moment(expandedSessionBlock.startDt).add(expandedSessionBlock.duration, 'minutes');
    } else {
      minDt = currentDayIdx === 0 ? moment(eventStart) : moment(currentDate).startOf('day').hour(8);
      maxDt = reachedLastDay
        ? moment(eventEnd).subtract(defaultContributionDuration, 'minutes')
        : moment(currentDate)
            .endOf('day')
            .subtract(19 * 60 + 59, 'seconds');
    }

    const currentEntryEndDts = currentEntries.map(e =>
      moment(e.startDt).add(e.duration, 'minutes')
    );
    const newDt = moment.min(maxDt, moment.max(minDt, ...currentEntryEndDts));
    const draftEntry = {
      startDt: newDt,
      duration: defaultContributionDuration,
      locationParent: eventLocationParent,
      locationData: {...eventLocationParent.location_data, inheriting: true},
    };
    dispatch(actions.setDraftEntry(draftEntry));
    openModal(DRAFT_ENTRY_MODAL, {
      eventId,
      entry: draftEntry,
      onClose: () => {
        dispatch(actions.setDraftEntry(null));
      },
    });
  };

  return (
    <div styleName="toolbar" ref={ref}>
      <div styleName="actions-bar">
        <Button basic onClick={addNewEntry} title={Translate.string('Add new entry')} size="tiny">
          <Icon name="plus" />
          <Translate>Add entry</Translate>
        </Button>
        <div styleName="right">
          {expandedSessionBlock && (
            <Button
              onClick={() => dispatch(actions.setExpandedSessionBlock(null))}
              title={Translate.string('Exit session block view')}
              icon="arrow left"
              circular
              size="tiny"
            />
          )}
          <Button
            onClick={() => dispatch(actions.toggleExpand())}
            title={isExpanded ? Translate.string('Exit Fullscreen') : Translate.string('Expand')}
            icon={isExpanded ? 'compress' : 'expand'}
            circular
            size="tiny"
          />
        </div>
        {/* TODO: (Ajob) The logic behind this component is broken.
                         Evaluate necessity then remove or fix */}
        {/* <ReviewChangesButton as={Menu.Item} styleName="action" /> */}
      </div>
    </div>
  );
}
