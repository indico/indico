// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import * as actions from './actions';
import ContributionEntry from './ContributionEntry';
import {useDraggable} from './dnd';
import {EntryPopup} from './EntryPopup';
import {ReduxState} from './reducers';
import * as selectors from './selectors';

import './DayTimetable.module.scss';

interface DraggableEntryProps {
  id: number;
  isChild?: boolean;
  [key: string]: any;
}

export function DraggableEntry({id, isChild = false, ...rest}: DraggableEntryProps) {
  const dispatch = useDispatch();
  const {
    listeners: _listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: `${id}`,
  });
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
    onMouseDown: (event: MouseEvent) => {
      if (event.button !== 0) {
        return;
      }

      onMouseDown();
      _listeners.onMouseDown(event);
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

  if (isSelected && !isDragging) {
    return (
      <EntryPopup
        trigger={entry}
        onClose={() => {
          dispatch(actions.deselectEntry());
        }}
        entry={{id, ...rest}}
      />
    );
  }

  return entry;
}

export function DraggableBlockEntry({id, ...rest}: DraggableEntryProps) {
  return <DraggableEntry id={id} {...rest} />;
}
