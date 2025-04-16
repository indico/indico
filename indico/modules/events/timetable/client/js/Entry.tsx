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
import {ReduxState} from './reducers';
import * as selectors from './selectors';

import './DayTimetable.module.scss';

export function DraggableEntry({id, ...rest}) {
  const dispatch = useDispatch();
  const {listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: `${id}`,
  });
  const popupsEnabled = useSelector(selectors.getPopupsEnabled);
  const isSelected = useSelector((state: ReduxState) =>
    selectors.makeIsSelectedSelector()(state, id)
  );

  const entry = (
    <ContributionEntry
      id={id}
      {...rest}
      listeners={listeners}
      setNodeRef={setNodeRef}
      transform={transform}
      isDragging={isDragging}
    />
  );

  if (popupsEnabled && isSelected && !isDragging) {
    return (
      <TimetablePopup
        trigger={entry}
        onClose={() => dispatch(actions.selectEntry(null))}
        entry={{id, ...rest}}
      />
    );
  }

  return entry;
}

export function DraggableBlockEntry({id, ...rest}) {
  const dispatch = useDispatch();
  const {listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: `${id}`,
  });
  const popupsEnabled = useSelector(selectors.getPopupsEnabled);
  const isSelected = useSelector((state: ReduxState) =>
    selectors.makeIsSelectedSelector()(state, id)
  );

  const entry = (
    <BlockEntry
      id={id}
      {...rest}
      listeners={listeners}
      setNodeRef={setNodeRef}
      transform={transform}
      isDragging={isDragging}
      selected={isSelected}
    />
  );

  if (popupsEnabled && isSelected && !isDragging) {
    return (
      <TimetablePopup
        trigger={entry}
        onClose={() => dispatch(actions.selectEntry(null))}
        entry={{id, ...rest}}
      />
    );
  }

  return entry;
}
