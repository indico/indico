// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {ConnectDragSource} from 'react-dnd';

interface SortableItemType {
  id: string;
  index: number;
  type: string;
  itemData?: object;
  moveItem: (dragIndex: number, hoverIndex: number) => void;
  separateHandle?: boolean;
  active: boolean;
  onDrop: () => void;
}

/**
 * A React hook to sort items using drag & drop.
 */
export declare function useSortableItem({
  type,
  moveItem,
  id,
  index,
  separateHandle,
  active,
  onDrop,
  itemData,
}: SortableItemType): [any, ConnectDragSource, object];

/**
 * A wrapper component to make a list of items sortable.
 */
export declare function SortableWrapper({
  accept,
  children,
  ...rest
}: {
  accept: string;
  children: React.ReactNode;
}): JSX.Element;
