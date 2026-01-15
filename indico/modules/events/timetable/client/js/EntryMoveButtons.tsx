import moment, {Moment} from 'moment';
import React from 'react';
import {useDispatch, useSelector} from 'react-redux/es';
import {ThunkDispatch} from 'redux-thunk';
import {Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

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

export function EntryMoveButtons({
  id: _id,
  startDt,
  duration: _duration,
  sessionBlockId,
}: EntryMoveButtonsProps) {
  const dispatch: ThunkDispatch<ReduxState, unknown, actions.Action> = useDispatch();
  const entries = useSelector((state: ReduxState) => selectors.getDayEntries(state));
  const currentDate = useSelector(selectors.getCurrentDate);
  const dtKey = getDateKey(currentDate);
  const currentDateEntries = entries[dtKey];
  const entry = (
    sessionBlockId
      ? (currentDateEntries.find(e => e.id === sessionBlockId) as BlockEntry).children
      : currentDateEntries
  ).find(e => e.id === _id);
  const filteredEntries = (
    sessionBlockId ? currentDateEntries.filter(e => e.id === sessionBlockId) : currentDateEntries
  ).filter(e => e.id !== _id);

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
    let newStartDt: Moment | null = null;

    for (const fe of filteredEntries) {
      if (fe.id === _id) {
        continue;
      }

      const feEnd = moment(fe.startDt).add(fe.duration, 'minutes');
      const targetStart = moment(startDt);

      if (feEnd.isSame(targetStart)) {
        _swapEntries(fe, entry);
        return;
      }

      if (targetStart.isAfter(feEnd) && (!newStartDt || feEnd.isAfter(newStartDt))) {
        newStartDt = moment(feEnd);
      }
    }

    _moveEntry(entry, newStartDt);

    e.stopPropagation();
  };

  const moveDown = e => {
    let newStartDt: Moment | null = null;

    for (const fe of filteredEntries) {
      if (fe.id === _id) {
        continue;
      }

      const feStart = moment(fe.startDt);
      const targetEnd = moment(startDt).add(_duration, 'minutes');

      if (feStart.isSame(targetEnd)) {
        _swapEntries(entry, fe);
        return;
      }

      if (feStart.isAfter(targetEnd) && (!newStartDt || feStart.isBefore(newStartDt))) {
        newStartDt = moment(feStart).subtract(_duration, 'minutes');
      }
    }

    _moveEntry(entry, newStartDt);

    e.stopPropagation();
  };

  return (
    <div styleName="mv-buttons-wrapper">
      <button type="button" title={Translate.string('Move up')} onClick={moveUp}>
        <Icon name="chevron up" />
      </button>
      <button type="button">
        <Icon name="chevron down" title={Translate.string('Move down')} onClick={moveDown} />
      </button>
    </div>
  );
}
