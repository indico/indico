// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef} from 'react';
import {useDrag, useDrop} from 'react-dnd';

const mergeRefs = (...refs) => {
  return ref =>
    refs.forEach(r => {
      if (typeof r === 'function') {
        r(ref);
      } else {
        r.current = ref;
      }
    });
};

/**
 * A React hook to sort items using drag & drop.
 */
export function useSortableItem({
  type,
  moveItem,
  id,
  index,
  separateHandle,
  active,
  onDrop,
  itemData,
}) {
  if (active === undefined) {
    active = true;
  }
  const itemRef = useRef(null);
  const [, drop] = useDrop({
    accept: type,
    canDrop: () => false,
    hover: (item, monitor) => {
      if (!itemRef.current || !active) {
        return;
      }
      const dragIndex = item.index;
      const hoverIndex = index;
      // Don't replace items with themselves
      if (dragIndex === hoverIndex) {
        return;
      }
      // Determine rectangle on screen
      const hoverBoundingRect = itemRef.current.getBoundingClientRect();
      // Get vertical middle
      const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;
      // Determine mouse position
      const clientOffset = monitor.getClientOffset();
      // Get pixels to the top
      const hoverClientY = clientOffset.y - hoverBoundingRect.top;
      // Only perform the move when the mouse has crossed half of the items height
      // When dragging downwards, only move when the cursor is below 50%
      // When dragging upwards, only move when the cursor is above 50%
      // Dragging downwards
      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
        return;
      }
      // Dragging upwards
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
        return;
      }
      // Time to actually perform the action
      moveItem(dragIndex, hoverIndex);
      // Note: we're mutating the monitor item here!
      // Generally it's better to avoid mutations,
      // but it's good here for the sake of performance
      // to avoid expensive index searches.
      item.index = hoverIndex;
    },
  });
  const [{isDragging}, drag, preview] = useDrag({
    type,
    canDrag: () => active,
    item: () => ({id, index, originalIndex: index, ...(itemData || {})}),
    collect: monitor => ({
      isDragging: monitor.isDragging(),
    }),
    end: (item, monitor) => {
      const {index: curIndex, originalIndex} = item;
      const didDrop = monitor.didDrop();
      if (!didDrop) {
        moveItem(curIndex, originalIndex);
      } else if (onDrop) {
        onDrop(item);
      }
    },
  });
  const style = {opacity: isDragging ? 0.2 : 1};
  if (separateHandle) {
    return [drag, mergeRefs(preview, drop, itemRef), style];
  } else {
    return [null, mergeRefs(preview, drag, drop, itemRef), style];
  }
}

/** A wrapper that provides the outer dropping area around sortable items */
export function SortableWrapper({accept, children, ...rest}) {
  const [, drop] = useDrop({accept});
  return (
    <div ref={drop} {...rest}>
      {children}
    </div>
  );
}

SortableWrapper.propTypes = {
  accept: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};
