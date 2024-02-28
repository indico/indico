// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import noOverlap from 'react-big-calendar/lib/utils/layout-algorithms/no-overlap';

import {toClasses} from 'indico/react/util';

import {getConcurrentEntries, hasContributions, isChildOf} from './util';

import styles from './Timetable.module.scss';

const SESSION_BLOCK_WIDTH = 15;

export const entryStyleGetter = (entries, selected) => entry => {
  if (entry.parentId) {
    const parent = entries.find(e => isChildOf(entry, e));
    return {
      style: {
        color: parent?.color?.text,
        backgroundColor: parent?.color?.background,
        borderColor: parent?.color?.background,
      },
      className: toClasses({
        [styles['child-entry']]: true,
        [styles.selected]: selected && (selected.id === entry.id || selected.id === parent?.id),
      }),
    };
  }
  return {
    style: {
      color: entry.color?.text,
      backgroundColor: entry.color?.background,
      borderColor: entry.color?.background,
    },
    className: toClasses({
      [styles['parent-entry']]: hasContributions(entry, entries),
      [styles['placeholder-entry']]: entry.type === 'placeholder',
      [styles.selected]: selected?.id === entry.id,
    }),
  };
};

export const layoutAlgorithm = (allEntries, numColumns, compact) => props =>
  noOverlap(props).map(styledEntry => {
    // if it's a child-entry, remove the padding, and make it wider if in compact mode
    if (styledEntry.event.parentId) {
      const size = compact
        ? (100 - SESSION_BLOCK_WIDTH) / (100 / styledEntry.size - 1)
        : styledEntry.size;
      const left = compact
        ? SESSION_BLOCK_WIDTH + size * Math.max(styledEntry.idx - 1, 0)
        : styledEntry.style.left;
      const style = {
        ...styledEntry.style,
        left,
        width: `${size}%`,
        xOffset: `${left}%`,
      };
      return {...styledEntry, size, style};
    }

    // Check for empty space to the right of the entry
    // If there is empty space, expand the entry to fill it
    const {columnId} = styledEntry.event;
    const concurrentEntries = getConcurrentEntries(styledEntry.event, allEntries).sort(
      (a, b) => a.columnId - b.columnId
    );
    const rightConcurrent = concurrentEntries.filter(e => columnId < e.columnId);
    let gapSize;
    if (rightConcurrent.length > 0) {
      gapSize = rightConcurrent[0].columnId - columnId - 1;
    } else {
      gapSize = numColumns - columnId;
    }

    // make entries take up the full width if there are no concurrencies
    if (getConcurrentEntries(styledEntry.event, allEntries).length === 0) {
      const size = 100 * numColumns;
      const padding = 10 * (numColumns - 1) - (styledEntry.idx === 0 ? 0 : 3);
      const style = {
        ...styledEntry.style,
        left: 0,
        width: `calc(${size}% + ${padding}px)`,
        xOffset: 0,
      };
      return {...styledEntry, size, style};
    } else if (gapSize > 0) {
      const size = 100 * (1 + gapSize);
      const padding = 10 * gapSize - (styledEntry.idx === 0 ? 0 : 3);
      const style = {
        ...styledEntry.style,
        width: `calc(${size}% + ${padding}px)`,
      };
      return {...styledEntry, size, style};
    }
    // entries with children are squeezed when in compact mode
    if (compact && hasContributions(styledEntry.event, props.events)) {
      const style = {
        ...styledEntry.style,
        width: `${SESSION_BLOCK_WIDTH}%`,
      };
      return {...styledEntry, size: SESSION_BLOCK_WIDTH, style};
    }
    return styledEntry;
  });
