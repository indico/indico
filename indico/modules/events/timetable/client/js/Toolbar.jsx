// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useEffect, useRef} from 'react';
import {Navigate} from 'react-big-calendar';
import {useDispatch, useSelector} from 'react-redux';
import {Dropdown, Menu} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import * as selectors from './selectors';
import {getNumDays} from './util';

import './Toolbar.module.scss';

const SCROLL_STEP = 3;

const displayModes = {
  compact: {
    title: Translate.string('Compact timetable'),
    icon: 'minus square outline',
    next: 'full',
  },
  full: {title: Translate.string('Full timetable'), icon: 'plus square outline', next: 'compact'},
};

export default function Toolbar({date, localizer, onNavigate}) {
  const dispatch = useDispatch();
  const ref = useRef(null);
  const eventStart = useSelector(selectors.getEventStartDt);
  const numDays = useSelector(selectors.getEventNumDays);
  const canUndo = useSelector(selectors.canUndo);
  const canRedo = useSelector(selectors.canRedo);
  const maxDays = useSelector(selectors.getNavbarMaxDays);
  const offset = useSelector(selectors.getNavbarOffset);
  const _displayMode = useSelector(selectors.getDisplayMode);
  const displayMode = displayModes[_displayMode];
  const currentDayIdx = getNumDays(eventStart, date);

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

  const getDateFromIdx = idx => new Date(eventStart.getTime() + idx * 24 * 60 * 60 * 1000);

  const makeScrollHandler = newOffset => () => {
    if (currentDayIdx < newOffset) {
      onNavigate(Navigate.DATE, getDateFromIdx(newOffset));
    } else if (currentDayIdx >= newOffset + maxDays) {
      onNavigate(Navigate.DATE, getDateFromIdx(newOffset + maxDays - 1));
    }
    dispatch(actions.scrollNavbar(newOffset));
  };

  return (
    <div styleName="toolbar" ref={ref}>
      <Menu tabular>
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
              onClick={makeScrollHandler(0)}
              disabled={offset === 0}
              title={Translate.string('Go to start')}
              icon="angle double left"
              styleName="action"
            />
            <Menu.Item
              onClick={makeScrollHandler(Math.max(offset - SCROLL_STEP, 0))}
              disabled={offset === 0}
              title={Translate.string('Scroll left')}
              icon="angle left"
              styleName="action"
            />
          </>
        )}
        {[...Array(Math.min(numDays, maxDays)).keys()].map(n => {
          const d = getDateFromIdx(n + offset);
          return (
            <Menu.Item
              key={n}
              content={localizer.format(
                d,
                Translate.string('ddd DD/MM', 'momentjs date format for timetable tab headers')
              )}
              onClick={() => onNavigate(Navigate.DATE, d)}
              active={n + offset === currentDayIdx}
            />
          );
        })}
        {numDays > maxDays && (
          <>
            <Menu.Item
              onClick={makeScrollHandler(Math.min(offset + SCROLL_STEP, numDays - maxDays))}
              disabled={numDays - offset <= maxDays}
              title={Translate.string('Scroll right')}
              icon="angle right"
              position="right"
              styleName="action"
            />
            <Menu.Item
              onClick={makeScrollHandler(numDays - maxDays)}
              disabled={numDays - offset <= maxDays}
              title={Translate.string('Go to end')}
              icon="angle double right"
              styleName="action"
            />
          </>
        )}
        <Menu.Item
          onClick={() => dispatch(actions.setDisplayMode(displayMode.next))}
          icon={displayMode.icon}
          position={numDays <= maxDays ? 'right' : undefined}
          styleName="action"
          title={displayMode.title}
        />
        <Dropdown
          icon="add"
          styleName="action"
          direction="left"
          title={Translate.string('Add new')}
          item
        >
          <Dropdown.Menu>
            <Dropdown.Header content={Translate.string('Add new')} />
            <Dropdown.Item
              text={Translate.string('Session block')}
              icon="calendar alternate outline"
            />
            <Dropdown.Item text={Translate.string('Contribution')} icon="file alternate outline" />
            <Dropdown.Item text={Translate.string('Break')} icon="coffee" />
          </Dropdown.Menu>
        </Dropdown>
      </Menu>
    </div>
  );
}

Toolbar.propTypes = {
  date: PropTypes.instanceOf(Date).isRequired,
  localizer: PropTypes.object.isRequired,
  onNavigate: PropTypes.func.isRequired,
};
