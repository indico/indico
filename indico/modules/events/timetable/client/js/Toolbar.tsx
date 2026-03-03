// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React, {useEffect, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Header, Icon, Label, Menu} from 'semantic-ui-react';

import PublicationStateSwitch from 'indico/modules/events/contributions/PublicationStateSwitch';
import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {DRAFT_ENTRY_MODAL, useModal} from './ModalContext';
import * as selectors from './selectors';
import {ReduxState} from './types';
import {getDiffInDays} from './utils';

import './Toolbar.module.scss';

function SessionBlockToolbar() {
  const dispatch = useDispatch();
  const expandedSessionBlock = useSelector(selectors.getExpandedSessionBlock);
  const {title, colors, sessionId} = expandedSessionBlock ?? {};
  // (Ajob) Did not want to use sessionTitle property to get title, as
  //        it would not change when a session is changed in the future due
  //        to it simply being an appended value.
  const session = useSelector((state: ReduxState) => selectors.getSessionById(state, sessionId));

  if (!expandedSessionBlock) {
    return null;
  }

  const sessionColors = {
    backgroundColor: `${colors.backgroundColor}55`,
    color: colors.color,
  };

  return (
    <Menu tabular styleName="timetable-bar block">
      <Label size="small" styleName="session" style={{...sessionColors}}>
        {session.title}
      </Label>
      <Header as="h3" styleName="header">
        <span>{title}</span>
      </Header>
      <Button
        basic
        size="mini"
        onClick={() => dispatch(actions.setExpandedSessionBlock(null))}
        styleName="close-btn"
      >
        <Icon name="close" />
        <Translate>Close session block view</Translate>
      </Button>
    </Menu>
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
  const canUndo = useSelector(selectors.canUndo);
  const canRedo = useSelector(selectors.canRedo);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const isExpanded = useSelector(selectors.getIsExpanded);
  const currentDate = useSelector(selectors.getCurrentDate);
  const currentEntries = useSelector(selectors.getCurrentEntries);
  const expandedSessionBlock = useSelector(selectors.getExpandedSessionBlock);
  const defaultContributionDuration = useSelector(selectors.getDefaultContribDurationMinutes);
  const eventLocationParent = useSelector(selectors.getEventLocationParent);
  const currentDayIdx = getDiffInDays(eventStart, currentDate);
  const currentDayIdxRef = useRef<number>(currentDayIdx);
  const reachedLastDay = currentDayIdx >= numDays - 1;

  const gradientWidth = 10;
  const dayWidth = 60;

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
      <Menu compact secondary styleName="actions-bar">
        <Menu.Item
          onClick={() => dispatch(actions.toggleShowUnscheduled())}
          title={
            showUnscheduled
              ? // TODO: (Ajob) Rename to 'show draft entries' or something like that
                //              once we have changed this sidemenu's features.
                Translate.string('Hide unscheduled contributions')
              : Translate.string('Show unscheduled contributions')
          }
          styleName="action"
        >
          <Icon.Group>
            <Icon name="grid layout" />
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
      {expandedSessionBlock && <SessionBlockToolbar />}
      {!expandedSessionBlock && numDays > 1 && (
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
