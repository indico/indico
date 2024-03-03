// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Navigate} from 'react-big-calendar';
import {Dropdown, Menu} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './Toolbar.module.scss';

const MAX_DAYS = 9;
const SCROLL_STEP = 3;

export default function Toolbar({date, localizer, onNavigate}) {
  const [offset, setOffset] = useState(0);
  // TODO replace these with a selector
  const eventStart = new Date(2023, 4, 8);
  const eventEnd = new Date(2023, 5, 12);
  const numDays = (eventEnd - eventStart) / (24 * 60 * 60 * 1000) + 1;

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
      <Dropdown
        icon="add"
        className={numDays <= MAX_DAYS ? 'right' : undefined}
        styleName="action"
        direction="left"
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
