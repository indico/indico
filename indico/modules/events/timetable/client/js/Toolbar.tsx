// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Moment} from 'moment';
import React, {useCallback, useEffect, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Dropdown, Icon, Label, Menu, Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import NewEntryDropdown from './components/NewEntryDropdown';
import * as selectors from './selectors';

import './Toolbar.module.scss';

const SCROLL_STEP = 3;

const displayModes = [
  {
    name: 'compact',
    title: Translate.string('Compact', 'timetable display mode'),
    icon: 'minus square outline',
  },
  {
    name: 'full',
    title: Translate.string('Full', 'timetable display mode'),
    icon: 'plus square outline',
  },
  {
    name: 'blocks',
    title: Translate.string('Blocks', 'timetable display mode'),
    icon: 'block layout',
  },
];

export default function Toolbar({
  date,
  onNavigate,
}: {
  date: Moment;
  onNavigate: (dt: Moment) => void;
}) {
  const dispatch = useDispatch();
  const ref = useRef(null);
  const eventStart = useSelector(selectors.getEventStartDt);
  const numDays = useSelector(selectors.getEventNumDays);
  const numUnscheduled = useSelector(selectors.getNumUnscheduled);
  const canUndo = useSelector(selectors.canUndo);
  const canRedo = useSelector(selectors.canRedo);
  const error = useSelector(selectors.getError);
  const maxDays = useSelector(selectors.getNavbarMaxDays);
  const offset = useSelector(selectors.getNavbarOffset);
  const displayMode = useSelector(selectors.getDisplayMode);
  const showAllTimeslots = useSelector(selectors.showAllTimeslots);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  // (Ajob) Math.ceil and float number allows this to work for a difference of a day
  // but less than 24h, also across multiple months. Hence the 'true'.
  const currentDayIdx = Math.ceil(date.diff(eventStart, 'days', true));

  console.log('numdays', numDays)

  const handleResize = useCallback(() => {
    dispatch(actions.resizeWindow(ref.current.clientWidth, currentDayIdx));
  }, [currentDayIdx, dispatch]);

  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [handleResize]);

  const getDateFromIdx = idx => eventStart.clone().add(idx, 'days');

  const makeScrollHandler = (newOffset, navigateTo = null, mouseDown = false) => e => {
    if (mouseDown && e.buttons !== 1) {
      return;
    }
    if (typeof navigateTo === 'number') {
      onNavigate(getDateFromIdx(navigateTo));
    } else if (currentDayIdx < newOffset) {
      onNavigate(getDateFromIdx(newOffset));
    } else if (currentDayIdx >= newOffset + maxDays) {
      onNavigate(getDateFromIdx(newOffset + maxDays));
    }
    dispatch(actions.scrollNavbar(newOffset));
  };

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
      <Menu tabular>
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
            <Icon name={showUnscheduled ? 'eye slash' : 'eye'} corner="bottom right" />
            {!showUnscheduled && (
              <Label
                color={numUnscheduled ? 'red' : null}
                size="mini"
                content={numUnscheduled}
                floating
                circular
              />
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
        {numDays > maxDays && (
          <>
            <Menu.Item
              onClick={makeScrollHandler(0, 0)}
              onMouseEnter={makeScrollHandler(0, 0, true)}
              disabled={offset === 0}
              title={Translate.string('Go to start')}
              icon="angle double left"
              styleName="action"
            />
            <Menu.Item
              onClick={makeScrollHandler(Math.max(offset - SCROLL_STEP, 0))}
              onMouseEnter={makeScrollHandler(Math.max(offset - SCROLL_STEP, 0), null, true)}
              disabled={offset === 0}
              title={Translate.string('Scroll left')}
              icon="angle left"
              styleName="action"
            />
          </>
        )}
        <Menu.Item fitted styleName="days">
          <div styleName="gradient" />
          {[...Array(Math.min(numDays, numDays)).keys()].map(n => {
            const d = getDateFromIdx(n + offset);
            return (
              <Menu.Item
                key={n}
                content={d.format('ddd DD/MM')}
                onClick={() => onNavigate(d)}
                active={n + offset === currentDayIdx}
              />
            );
          })}
          <div styleName="gradient" />
        </Menu.Item>
        {numDays > maxDays && (
          <>
            <Menu.Item
              onClick={makeScrollHandler(Math.min(offset + SCROLL_STEP, numDays - maxDays))}
              onMouseEnter={makeScrollHandler(
                Math.min(offset + SCROLL_STEP, numDays - maxDays),
                null,
                true
              )}
              disabled={numDays - offset <= maxDays}
              title={Translate.string('Scroll right')}
              icon="angle right"
              position="right"
              styleName="action"
            />
            <Menu.Item
              onClick={makeScrollHandler(numDays - maxDays, numDays)}
              onMouseEnter={makeScrollHandler(numDays - maxDays, numDays, true)}
              disabled={numDays - offset <= maxDays}
              title={Translate.string('Go to end')}
              icon="angle double right"
              styleName="action"
            />
          </>
        )}
        <Dropdown
          icon="columns"
          styleName="action"
          className={numDays <= maxDays ? 'right' : undefined}
          direction="left"
          title={Translate.string('Display mode')}
          item
        >
          <Dropdown.Menu>
            {displayModes.map(({name, title, icon}) => (
              <Dropdown.Item
                key={name}
                text={title}
                icon={icon}
                onClick={() => dispatch(actions.setDisplayMode(name))}
                active={displayMode === name}
              />
            ))}
            <Dropdown.Divider />
            <Dropdown.Item
              text={Translate.string('Show all timeslots')}
              icon="clock outline"
              onClick={e => {
                e.stopPropagation();
                dispatch(actions.toggleShowAllTimeslots());
              }}
              active={showAllTimeslots}
            />
          </Dropdown.Menu>
        </Dropdown>
        <NewEntryDropdown
          icon="add"
          styleName="action"
          direction="left"
          title={Translate.string('Add new')}
          item
        />
        {/* <ReviewChangesButton as={Menu.Item} styleName="action" /> */}
      </Menu>
    </div>
  );
}
