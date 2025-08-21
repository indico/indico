// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React, {Ref, useEffect, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon, Label, Menu, Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import PublicationStateSwitch from '../../../contributions/client/js/PublicationStateSwitch';

import * as actions from './actions';
import * as selectors from './selectors';
import './Toolbar.module.scss';

export default function Toolbar({
  date,
  onNavigate,
}: {
  date: Moment;
  onNavigate: (dt: Moment) => void;
}) {
  const dispatch = useDispatch();
  const ref = useRef(null);
  const daysBarRef = useRef<HTMLDivElement | null>(null);
  const eventId = useSelector(selectors.getEventId);
  const eventStart = useSelector(selectors.getEventStartDt);
  const eventEnd = useSelector(selectors.getEventEndDt);
  const numDays = useSelector(selectors.getEventNumDays);
  const numUnscheduled = useSelector(selectors.getNumUnscheduled);
  const canUndo = useSelector(selectors.canUndo);
  const canRedo = useSelector(selectors.canRedo);
  const error = useSelector(selectors.getError);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const isExpanded = useSelector(selectors.getIsExpanded);
  const currentDate = useSelector(selectors.getCurrentDate);
  const currentDayEntries = useSelector(selectors.getCurrentDayEntries);
  const defaultContributionDuration = useSelector(selectors.getDefaultContribDurationMinutes);
  // Math.ceil and float number allows this to work for a difference of a day
  // but less than 24h, also across multiple months. Hence the 'true'.
  const currentDayIdx = Math.ceil(date.diff(eventStart, 'days', true));
  const currentDayIdxRef = useRef<number>(currentDayIdx);
  const reachedLastDay = currentDayIdx >= numDays - 1;

  const gradientWidth = 10;
  const dayWidth = 60;

  const getDateFromIdx = (idx): Moment => eventStart.clone().add(idx, 'days');

  const scrollToDay = (dayIndex: number, behavior: ScrollBehavior = 'instant') => {
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
    const daysPerPage = Math.floor((daysBarRef.current.clientWidth - gradientWidth) / dayWidth);
    const dayDelta = daysPerPage * pageDelta;
    scrollByDay(dayDelta, behavior);
  };

  const addNewEntry = () => {
    const minDt =
      currentDayIdx === 0
        ? moment(eventStart)
        : moment(currentDate)
            .startOf('day')
            .hour(8);
    const maxDt = reachedLastDay
      ? moment(eventEnd).subtract(defaultContributionDuration, 'minutes')
      : moment(currentDate)
          .endOf('day')
          .subtract(19 * 60 + 59, 'seconds');
    const currentDayEntryEndDts = currentDayEntries.map(e =>
      moment(e.startDt).add(e.duration, 'minutes')
    );
    const newDt = moment.min(maxDt, moment.max(minDt, ...currentDayEntryEndDts));
    const draftEntry = {startDt: newDt, duration: defaultContributionDuration};
    dispatch(actions.setDraftEntry(draftEntry));
  };

  useEffect(() => {
    scrollToDay(currentDayIdxRef.current);
  }, [currentDayIdxRef]);

  return (
    <div styleName="toolbar" ref={ref}>
      {error && (
        <Message
          warning
          icon="warning sign"
          header={error.title}
          content={<p>{error.content}</p>}
          onDismiss={() => dispatch(actions.dismissError())}
        />
      )}
      <Menu compact secondary styleName="actions-bar">
        <Menu.Item
          onClick={() => dispatch(actions.toggleShowUnscheduled())}
          disabled={!showUnscheduled && numUnscheduled === 0}
          title={
            showUnscheduled
              ? Translate.string('Hide unscheduled contributions')
              : Translate.string('Show unscheduled contributions')
          }
          styleName="action"
        >
          <Icon.Group>
            <Icon name="file alternate outline" />
            {!showUnscheduled && (
              <Label color="red" size="mini" content={numUnscheduled} floating circular />
            )}
          </Icon.Group>
        </Menu.Item>
        <Menu.Item
          onClick={() => dispatch(actions.undoChange())}
          disabled={!canUndo}
          title={Translate.string('Undo change')}
          icon="undo"
          styleName="action"
        />
        <Menu.Item
          onClick={() => dispatch(actions.redoChange())}
          disabled={!canRedo}
          title={Translate.string('Redo change')}
          icon="redo"
          styleName="action"
        />
        <Menu.Item className="right" styleName="action">
          <PublicationStateSwitch
            eventId={eventId}
            onSuccess={() => dispatch(actions.toggleDraft())}
            basic
          />
        </Menu.Item>
        <Menu.Item
          onClick={addNewEntry}
          title={Translate.string('Add new entry')}
          icon="plus"
          styleName="action"
        />
        <Menu.Item
          onClick={() => dispatch(actions.toggleExpand())}
          title={isExpanded ? Translate.string('Exit Fullscreen') : Translate.string('Expand')}
          icon={isExpanded ? 'compress' : 'expand'}
          styleName="action"
        />
        {/* TODO: (Ajob) The logic behind this component is broken.
                         Evaluate necessity then remove or fix */}
        {/* <ReviewChangesButton as={Menu.Item} styleName="action" /> */}
      </Menu>
      {numDays > 1 && (
        <Menu tabular styleName="timetable-bar">
          {numDays > 2 && (
            <Menu.Item
              onClick={() => scrollByPage(-1)}
              disabled={currentDayIdx === 0}
              title={Translate.string('Previous page')}
              icon="angle double left"
              styleName="action"
            />
          )}
          <Menu.Item
            onClick={() => scrollByDay(-1)}
            disabled={currentDayIdx === 0}
            title={Translate.string('Previous day')}
            icon="angle left"
            styleName="action"
          />
          <Menu.Item fitted styleName="days-wrapper">
            <div ref={daysBarRef} styleName="days">
              <div styleName="gradient" />
              {[...Array(numDays).keys()].map(n => {
                const d = getDateFromIdx(n);
                const isActive = n === currentDayIdx;
                return (
                  <Menu.Item
                    fitted="horizontally"
                    key={n}
                    onClick={() => navigateToDayNumber(n)}
                    styleName="day"
                    active={isActive}
                  >
                    <span styleName="day-month">{d.format('MMM')}</span>
                    <span styleName="day-number">{d.format('D')}</span>
                    <span styleName="day-name">{d.format('ddd')}</span>
                  </Menu.Item>
                );
              })}
              <div styleName="gradient" />
            </div>
          </Menu.Item>
          <Menu.Item
            onClick={() => scrollByDay(1)}
            disabled={reachedLastDay}
            title={Translate.string('Next day')}
            icon="angle right"
            position="right"
            styleName="action"
          />
          {numDays > 2 && (
            <Menu.Item
              onClick={() => scrollByPage(1)}
              disabled={reachedLastDay}
              title={Translate.string('Next page')}
              icon="angle double right"
              styleName="action"
            />
          )}
        </Menu>
      )}
    </div>
  );
}
