// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect, useRef, useState} from 'react';
import {useSelector, useDispatch} from 'react-redux';

import * as actions from './actions';
import NewEntryDropdown from './components/NewEntryDropdown';
import * as selectors from './selectors';
import {entrySchema, entryTypes, getEndDt, isChildOf} from './util';

import './Entry.module.scss';
import {
  Button,
  ButtonGroup,
  Card,
  Dropdown,
  DropdownHeader,
  DropdownItem,
  DropdownMenu,
  Icon,
  Popup,
} from 'semantic-ui-react';
import EntryDetails from './EntryDetails';
import moment from 'moment';
import {createPortal} from 'react-dom';

export default function Entry({event: entry}) {
  const {type, title} = entry;
  const contributions = useSelector(selectors.getVisibleChildren);
  const displayMode = useSelector(selectors.getDisplayMode);

  if (type === 'placeholder') {
    return <NewEntryDropdown icon={null} open />;
  }

  const startTime = moment(entry.start).format('HH:mm');
  const endTime = moment(getEndDt(entry)).format('HH:mm');
  const duration = entry.duration;
  const showSingleLine = duration <= 15;
  const hasContribs = contributions.some(c => isChildOf(c, entry));

  const compactTitle = (
    <div styleName="compact-title" style={{fontSize: 15}}>
      {type !== 'contribution' && <Icon name={entryTypes[type].icon} />} {title}
    </div>
  );

  const fullTitle = (
    <div styleName="entry-title">
      {showSingleLine && (
        <div style={{fontSize: 15, display: 'flex', gap: 6}}>
          {type !== 'contribution' && <Icon name={entryTypes[type].icon} />}
          <span>
            {entryTypes[type].formatTitle(entry)}, {startTime} - {endTime}
          </span>
        </div>
      )}
      {!showSingleLine && (
        <>
          <div style={{fontSize: 15, display: 'flex', gap: 6}}>
            {type !== 'contribution' && <Icon name={entryTypes[type].icon} />}
            <span>{entryTypes[type].formatTitle(entry)}</span>
          </div>
          <div style={{fontSize: 15, marginTop: 3}}>
            {startTime} - {endTime}
          </div>
        </>
      )}
    </div>
  );

  return (
    <div>
      {displayMode === 'compact' && hasContribs && compactTitle}
      {(displayMode !== 'compact' || !hasContribs) && fullTitle}
    </div>
  );
}

Entry.propTypes = {
  event: entrySchema.isRequired,
};
