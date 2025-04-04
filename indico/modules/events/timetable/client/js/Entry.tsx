// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';

import * as actions from './actions';
import BlockEntry from './BlockEntry';
import ContributionEntry from './ContributionEntry';
import {useDraggable} from './dnd';
import {TimetablePopup} from './entry_popups';
import * as selectors from './selectors';

import './DayTimetable.module.scss';

export function DraggableEntry({id, ...rest}) {
  const dispatch = useDispatch();
  const {listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: `${id}`,
  });
  const popupsEnabled = useSelector(selectors.getPopupsEnabled);
  const selectedId = useSelector(selectors.getSelectedId);
  const selected = useSelector(selectors.getSelectedEntry);

  if (popupsEnabled && selected && id === selectedId) {
    const trigger = (
      <ContributionEntry
        id={id}
        {...rest}
        listeners={listeners}
        setNodeRef={setNodeRef}
        transform={transform}
        isDragging={isDragging}
      />
    );
    return (
      <TimetablePopup
        trigger={trigger}
        onClose={() => dispatch(actions.selectEntry(null))}
        entry={selected}
      />
    );
  }

  return (
    <ContributionEntry
      id={id}
      {...rest}
      listeners={listeners}
      setNodeRef={setNodeRef}
      transform={transform}
      isDragging={isDragging}
    />
  );
}

export function DraggableBlockEntry({id, ...rest}) {
  const dispatch = useDispatch();
  const {listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: `${id}`,
  });
  const popupsEnabled = useSelector(selectors.getPopupsEnabled);
  const selectedId = useSelector(selectors.getSelectedId);
  const selected = useSelector(selectors.getSelectedEntry);

  if (popupsEnabled && selected && id === selectedId) {
    const trigger = (
      <BlockEntry
        id={id}
        {...rest}
        listeners={listeners}
        setNodeRef={setNodeRef}
        transform={transform}
        isDragging={isDragging}
      />
    );
    return (
      <TimetablePopup
        trigger={trigger}
        onClose={() => dispatch(actions.selectEntry(null))}
        entry={selected}
      />
    );
  }

  return (
    <BlockEntry
      id={id}
      {...rest}
      listeners={listeners}
      setNodeRef={setNodeRef}
      transform={transform}
      isDragging={isDragging}
    />
  );
}
