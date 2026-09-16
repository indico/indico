// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React, {useCallback, useEffect, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Header, Label} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import * as selectors from './selectors';
import {ReduxState} from './types';
import {getEntryColors} from './utils';

import './TimetableDayControls.module.scss';

interface TimetableDayControlsProps {
  onNavigate: (dt: Moment) => void;
  isSessionBlockExpanded: boolean;
  numDays: number;
  eventStart: Moment;
  currentDayIdx: number;
}

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
    <>
      <Label size="small" styleName="session" style={{...colors}}>
        {session.title}
      </Label>
      {title && <Header styleName="header">{title}</Header>}
    </>
  );
}

export function TimetableDayControls({
  isSessionBlockExpanded,
  onNavigate,
  numDays,
  currentDayIdx,
  eventStart,
}: TimetableDayControlsProps) {
  const daysBarRef = useRef<HTMLDivElement | null>(null);
  const currentDayIdxRef = useRef<number>(currentDayIdx);

  const reachedLastDay = currentDayIdx >= numDays - 1;
  const dayWidth = 75;

  const getDateFromIdx = (idx: number): Moment => eventStart.clone().add(idx, 'days');

  const scrollToDay = (dayIndex: number, behavior: ScrollBehavior = 'instant') => {
    if (!daysBarRef.current) {
      return;
    }
    const barWidth = daysBarRef.current.clientWidth;
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
    const daysPerPage = Math.floor(daysBarRef.current.clientWidth / dayWidth);
    const dayDelta = daysPerPage * pageDelta;
    scrollByDay(dayDelta, behavior);
  };

  useEffect(() => {
    scrollToDay(currentDayIdxRef.current);
  }, [currentDayIdxRef]);

  return (
    <div styleName="day-controls">
      {isSessionBlockExpanded && <SessionBlockToolbar />}
      {!isSessionBlockExpanded && numDays > 1 && (
        <>
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
        </>
      )}
    </div>
  );
}
