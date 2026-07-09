// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React, {useCallback, useEffect, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Header, Icon, Label} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {DRAFT_ENTRY_MODAL, useModal} from './ModalContext';
import * as selectors from './selectors';
import {ReduxState} from './types';
import {getDiffInDays, getEntryColors} from './utils';

import './Toolbar.module.scss';

function SessionBlockToolbar() {
  const dispatch = useDispatch();
  const expandedSessionBlock = useSelector(selectors.getExpandedSessionBlock);
  const {title, sessionId} = expandedSessionBlock ?? {};
  const session = useSelector((state: ReduxState) => selectors.getSessionById(state, sessionId));
  const colors = getEntryColors(expandedSessionBlock, session);

  const closeExpandedBlock = useCallback(
    () => dispatch(actions.setExpandedSessionBlock(null)),
    [dispatch]
  );

  useEffect(() => {
    if (!expandedSessionBlock) {
      return;
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeExpandedBlock();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [expandedSessionBlock, closeExpandedBlock]);

  if (!expandedSessionBlock) {
    return null;
  }

  return (
    <div styleName="timetable-bar block">
      <Label size="small" styleName="session" style={{...colors}}>
        {session.title}
      </Label>
      {title && <Header styleName="header">{title}</Header>}
    </div>
  );
}

export default function Toolbar({onNavigate}: {onNavigate: (dt: Moment) => void}) {
  const dispatch = useDispatch();
  const {openModal} = useModal();

  const ref = useRef(null);
  const daysBarRef = useRef<HTMLDivElement | null>(null);
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
  const currentDayIdxRef = useRef<number>(currentDayIdx);
  const reachedLastDay = currentDayIdx >= numDays - 1;

  const gradientWidth = 30;
  const dayWidth = 75;

  const getDateFromIdx = (idx: number): Moment => eventStart.clone().add(idx, 'days');

  const scrollToDay = (dayIndex: number, behavior: ScrollBehavior = 'instant') => {
    if (!daysBarRef.current) {
      return;
    }
    const barWidth = daysBarRef.current.clientWidth - gradientWidth;
    const left = dayIndex * dayWidth - barWidth / 2 + dayWidth / 2;
    daysBarRef.current.scrollTo({left, behavior});
  };

  const navigateToDayNumber = (num: number, scrollBehavior: ScrollBehavior = 'smooth') => {
    scrollToDay(num, scrollBehavior);
    onNavigate(getDateFromIdx(num));
  };

  const scrollByDay = (dayDelta: number, behavior: ScrollBehavior = 'smooth') => {
    const directionSign = Math.sign(dayDelta);
    const newDay =
      directionSign === 1
        ? Math.min(currentDayIdx + dayDelta, numDays - 1)
        : Math.max(currentDayIdx + dayDelta, 0);
    navigateToDayNumber(newDay, behavior);
  };

  const scrollByPage = (pageDelta: number, behavior: ScrollBehavior = 'smooth') => {
    if (!daysBarRef.current) {
      console.error('no daysBarRef');
      return;
    }
    const daysPerPage = Math.floor((daysBarRef.current.clientWidth - gradientWidth) / dayWidth);
    const dayDelta = daysPerPage * pageDelta;
    scrollByDay(dayDelta, behavior);
  };

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

  useEffect(() => {
    scrollToDay(currentDayIdxRef.current);
  }, [currentDayIdxRef]);

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
      {expandedSessionBlock && <SessionBlockToolbar />}
      {!expandedSessionBlock && numDays > 1 && (
        <div styleName="timetable-bar">
          {numDays > 2 && (
            <Button
              onClick={() => scrollByPage(-1)}
              disabled={currentDayIdx === 0}
              title={Translate.string('Previous page')}
              icon="angle double left"
              styleName="nav-button"
            />
          )}
          <Button
            onClick={() => scrollByDay(-1)}
            disabled={currentDayIdx === 0}
            title={Translate.string('Previous day')}
            icon="angle left"
            styleName="nav-button"
          />
          <div styleName="days-wrapper">
            <div ref={daysBarRef} styleName="days">
              <div styleName="gradient" />
              {[...Array(numDays).keys()].map(n => {
                const d = getDateFromIdx(n);
                const isActive = n === currentDayIdx;

                return (
                  <Button
                    key={n}
                    onClick={() => navigateToDayNumber(n)}
                    styleName={`day ${isActive ? 'active' : ''}`}
                  >
                    <div styleName="day-badge">
                      <div styleName="day-number">
                        {new Intl.DateTimeFormat(moment.locale(), {
                          month: 'short',
                          day: 'numeric',
                        }).format(d.toDate())}
                      </div>
                      <div styleName="day-name">{d.format('ddd')}</div>
                    </div>
                  </Button>
                );
              })}
              <div styleName="gradient" />
            </div>
          </div>
          <Button
            onClick={() => scrollByDay(1)}
            disabled={reachedLastDay}
            title={Translate.string('Next day')}
            icon="angle right"
            position="right"
            styleName="nav-button"
          />
          {numDays > 2 && (
            <Button
              onClick={() => scrollByPage(1)}
              disabled={reachedLastDay}
              title={Translate.string('Next page')}
              icon="angle double right"
              styleName="nav-button"
            />
          )}
        </div>
      )}
    </div>
  );
}
