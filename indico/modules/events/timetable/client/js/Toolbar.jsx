// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Navigate} from 'react-big-calendar';
import {useDispatch, useSelector} from 'react-redux';
import {Dropdown, Menu} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import * as selectors from './selectors';

import './Toolbar.module.scss';

const MAX_DAYS = 9;
const SCROLL_STEP = 3;

export default function Toolbar({date, localizer, onNavigate}) {
  const dispatch = useDispatch();
  const compactMode = useSelector(selectors.isCompactModeEnabled);
  const eventStart = useSelector(selectors.getEventStartDt);
  const numDays = useSelector(selectors.getEventNumDays);
  const [offset, setOffset] = useState(0);

  return (
    <Menu styleName="toolbar" tabular>
      {numDays > MAX_DAYS && (
        <>
          <Menu.Item
            onClick={() => setOffset(0)}
            disabled={offset === 0}
            icon="angle double left"
            styleName="action"
          />
          <Menu.Item
            onClick={() => setOffset(Math.max(offset - SCROLL_STEP, 0))}
            disabled={offset === 0}
            icon="angle left"
            styleName="action"
          />
        </>
      )}
      {[...Array(Math.min(numDays, MAX_DAYS)).keys()].map(n => {
        const d = new Date(eventStart.getTime() + (n + offset) * 24 * 60 * 60 * 1000);
        return (
          <Menu.Item
            key={n}
            name={localizer.format(d, 'ddd DD/MM')} // TODO somehow provide context: pgettext('momentjs date format for timetable tab headers', 'ddd DD/MM')
            onClick={() => onNavigate(Navigate.DATE, d)}
            active={d.toDateString() === date.toDateString()}
          />
        );
      })}
      {numDays > MAX_DAYS && (
        <>
          <Menu.Item
            onClick={() => setOffset(Math.min(offset + SCROLL_STEP, numDays - MAX_DAYS))}
            disabled={numDays - offset <= MAX_DAYS}
            icon="angle right"
            position="right"
            styleName="action"
          />
          <Menu.Item
            onClick={() => setOffset(numDays - MAX_DAYS)}
            disabled={numDays - offset <= MAX_DAYS}
            icon="angle double right"
            styleName="action"
          />
        </>
      )}
      <Menu.Item
        onClick={() => dispatch(actions.toggleCompactMode())}
        icon={compactMode ? 'plus square outline' : 'minus square outline'}
        position={numDays <= MAX_DAYS ? 'right' : undefined}
        styleName="action"
        title={
          compactMode
            ? Translate.string('Show full timetable')
            : Translate.string('Show compact timetable')
        }
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
          <Dropdown.Item text={Translate.string('Session block')} icon="clock" />
          <Dropdown.Item text={Translate.string('Contribution')} icon="file alternate" />
          <Dropdown.Item text={Translate.string('Break')} icon="coffee" />
        </Dropdown.Menu>
      </Dropdown>
    </Menu>
  );
}

Toolbar.propTypes = {
  date: PropTypes.instanceOf(Date).isRequired,
  localizer: PropTypes.object.isRequired,
  onNavigate: PropTypes.func.isRequired,
};
