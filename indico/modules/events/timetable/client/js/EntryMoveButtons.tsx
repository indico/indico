// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React from 'react';
import {useDispatch, useSelector} from 'react-redux/es';
import {ThunkDispatch} from 'redux-thunk';
import {Icon} from 'semantic-ui-react';

import * as actions from './actions';
import * as selectors from './selectors';
import {ReduxState, BlockEntry, Entry, EntryType} from './types';
import {getDateKey} from './utils';

import './Entry.module.scss';

interface EntryMoveButtonsProps {
  id: string;
  startDt: Moment;
  duration: number;
  sessionBlockId?: string;
}

export function EntryMoveButtons({id, startDt, duration, sessionBlockId}: EntryMoveButtonsProps) {
  const dispatch: ThunkDispatch<ReduxState, unknown, actions.Action> = useDispatch();
  const currentDate = useSelector(selectors.getCurrentDate);
  const dtKey = getDateKey(currentDate);
  const entries = useSelector((state: ReduxState) => selectors.getDayEntries(state));
  const currentDateEntries = entries[dtKey];
  const parent = sessionBlockId
    ? (currentDateEntries.find(e => e.id === sessionBlockId) as BlockEntry)
    : null;
  const entry = (parent ? (parent?.children ?? []) : currentDateEntries).find(e => e.id === id);
  const filteredEntries = (parent ? (parent?.children ?? []) : currentDateEntries).filter(
    e => e.id !== id
  );

  // TODO: (Ajob) Evaluate if we want to disable support for moving entries within groups
  //              (overlapping directly/indirectly). If so we can sort the entries instead
  //              and calculate overlap to disable the buttons accordingly. Still would work
  //              for above/below calculation.
  const _getAdjacentEntries = () => {
    let above: Entry | null = null;
    let below: Entry | null = null;
    const targetStart = moment(startDt);
    const targetEnd = moment(startDt).add(duration, 'minutes');

    for (const fe of filteredEntries) {
      if (fe.id === id) {
        continue;
      }

      const feStart = moment(fe.startDt);
      const feEnd = moment(feStart).add(fe.duration, 'minutes');

      if (
        targetStart.isSameOrAfter(feEnd) &&
        (!above || feEnd.isAfter(moment(above.startDt).add(above.duration, 'minutes')))
      ) {
        above = fe;
      } else if (targetEnd.isSameOrBefore(feStart) && (!below || feStart.isBefore(below.startDt))) {
        below = fe;
      }
    }

    return [above, below];
  };

  const [above, below] = _getAdjacentEntries();

  const _getMovedChildrenByDelta = (parentEntry: BlockEntry, delta: number) =>
    parentEntry?.children.map(child => ({
      ...child,
      startDt: moment(child.startDt).add(delta, 'minutes'),
    }));

  const _moveEntry = (e: Entry, newStartDt: Moment) => {
    const newEntry = {...e, startDt: newStartDt};

    if (newStartDt) {
      if (newEntry.type === EntryType.SessionBlock && newEntry.children) {
        newEntry.children = _getMovedChildrenByDelta(
          newEntry as BlockEntry,
          newStartDt.diff(e.startDt, 'minutes')
        );
      }

      dispatch(
        actions.updateEntry(e.type, newEntry, dtKey, {
          start_dt: newEntry.startDt,
        })
      );
    }
  };

  const _swapEntries = (topEntry: Entry, bottomEntry: Entry) => {
    const topEntryNew = {
      ...topEntry,
      startDt: moment(topEntry.startDt).add(bottomEntry.duration, 'minutes'),
    };
    const bottomEntryNew = {...bottomEntry, startDt: moment(topEntry.startDt)};

    _moveEntry(topEntry, topEntryNew.startDt);
    _moveEntry(bottomEntry, bottomEntryNew.startDt);
  };

  const moveUp = e => {
    e.stopPropagation();

    const targetStart = moment(startDt);

    if (!above) {
      // TODO: (Ajob) Consider implementing snapping to top of calendar
      return;
    }

    const aboveEnd = moment(above.startDt).add(above.duration, 'minutes');

    if (aboveEnd.isSame(targetStart)) {
      _swapEntries(above, entry);
      return;
    }

    _moveEntry(entry, aboveEnd);
  };

  const moveDown = e => {
    e.stopPropagation();
    console.log('below', below?.title);

    const targetEnd = moment(startDt).add(duration, 'minutes');

    if (!below) {
      // TODO: (Ajob) Consider implementing snapping to bottom of calendar
      console.log('nothing below');
      return;
    }

    if (below.startDt.isSame(targetEnd)) {
      _swapEntries(entry, below);
      return;
    }

    _moveEntry(entry, moment(below.startDt).subtract(duration, 'minutes'));
  };

  return (
    (above || below) && (
      <div styleName="mv-buttons-wrapper">
        <button type="button" onClick={moveUp} disabled={!above}>
          <Icon name="chevron up" />
        </button>
        <button type="button" onClick={moveDown} disabled={!below}>
          <Icon name="chevron down" />
        </button>
      </div>
    )
  );
}
