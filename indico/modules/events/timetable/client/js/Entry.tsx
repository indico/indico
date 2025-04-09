// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import * as actions from './actions';
import BlockEntry from './BlockEntry';
import EntryContent from './ContributionEntry';
import {useDraggable} from './dnd';
import {TimetablePopup} from './EntryPopup';
import {ReduxState} from './reducers';
import * as selectors from './selectors';

import './DayTimetable.module.scss';

// export function DraggableBlockEntry({id, ...rest}) {
//   const dispatch = useDispatch();
//   const {listeners, setNodeRef, transform, isDragging} = useDraggable({
//     id: `${id}`,
//   });
//   const popupsEnabled = useSelector(selectors.getPopupsEnabled);
//   const selectedId = useSelector(selectors.getSelectedId);
//   const selected = useSelector(selectors.getSelectedEntry);

//   if (popupsEnabled && selected && id === selectedId) {
//     const trigger = (
//       <BlockEntry
//         id={id}
//         {...rest}
//         listeners={listeners}
//         setNodeRef={setNodeRef}
//         transform={transform}
//         isDragging={isDragging}
//       />
//     );
//     return (
//       <TimetablePopup
//         trigger={trigger}
//         onClose={() => dispatch(actions.selectEntry(null))}
//         entry={selected}
//       />
//     );
//   }

//   return (
//     <BlockEntry
//       id={id}
//       {...rest}
//       listeners={listeners}
//       setNodeRef={setNodeRef}
//       transform={transform}
//       isDragging={isDragging}
//     />
//   );
// }

export function DraggableEntry({id, isChild=false, ...rest}) {
  const dispatch = useDispatch();
  const {listeners: _listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: `${id}`,
  });
  const popupsEnabled = useSelector(selectors.getPopupsEnabled);
  const isSelected = useSelector((state: ReduxState) =>
    selectors.makeIsSelectedSelector()(state, id)
  );
  // Used to determine whether the entry was just clicked or actually dragged
  // if dragged, this prevents selecting the entry on drag end (and thus showing the popup)
  const isClick = useRef<boolean>(true);

  function onClick(e) {
    e.stopPropagation();
    if (isClick.current) {
      dispatch(actions.selectEntry(id));
    }
  }

  function onMouseDown() {
    isClick.current = true;
  }

  const listeners = {
    ..._listeners,
    onClick,
    onMouseDown: e => {
      onMouseDown();
      _listeners.onMouseDown(e);
    },
  };

  useEffect(() => {
    if (isDragging) {
      isClick.current = false;
      dispatch(actions.deselectEntry());
    }
  }, [dispatch, isDragging]);

  const entry = (
    <ContributionEntry
      id={id}
      isChild={isChild}
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
        onClose={() => dispatch(actions.deselectEntry())}
        entry={{id, ...rest}}
      />
    );
  }

  return entry;
}

export function DraggableBlockEntry({id, ...rest}) {
  const dispatch = useDispatch();
  const {listeners: _listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: `${id}`,
  });
  const popupsEnabled = useSelector(selectors.getPopupsEnabled);
  const isSelected = useSelector((state: ReduxState) =>
    selectors.makeIsSelectedSelector()(state, id)
  );
  // Used to determine whether the entry was just clicked or actually dragged
  // if dragged, this prevents selecting the entry on drag end (and thus showing the popup)
  const isClick = useRef<boolean>(true);

  function onClick(e) {
    e.stopPropagation();
    if (isClick.current) {
      dispatch(actions.selectEntry(id));
    }
  }

  function onMouseDown() {
    isClick.current = true;
  }

  const listeners = {
    ..._listeners,
    onClick,
    onMouseDown: e => {
      onMouseDown();
      _listeners.onMouseDown(e);
    },
  };

  useEffect(() => {
    if (isDragging) {
      isClick.current = false;
      dispatch(actions.deselectEntry());
    }
  }, [isDragging, dispatch]);

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
        onClose={() => dispatch(actions.deselectEntry())}
        entry={{id, ...rest}}
      />
    );
  }

  return entry;
}
