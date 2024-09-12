import React from 'react';

import BlockEntry from './BlockEntry';
import ContributionEntry from './ContributionEntry';
import {useDraggable, useDroppable} from './dnd';

import './DayTimetable.module.scss';

export function DraggableEntry({id, ...rest}) {
  const {listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: `${id}`,
  });

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
  const {listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: `${id}`,
  });

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
