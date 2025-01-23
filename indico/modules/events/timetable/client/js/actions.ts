// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

//TODO remove this
export * from './staticDataSlice';
export * from './entriesSlice';
export * from './sessionsSlice';
export * from './navigationSlice';
export * from './displaySlice';
export * from './openModalSlice';
export * from './experimentalSlice';

// redux actions
export const REGISTER_DROPPABLE = 'REGISTER_DROPPABLE';
export const UNREGISTER_DROPPABLE = 'UNREGISTER_DROPPABLE';
export const SET_DROPPABLE_DATA = 'SET_DROPPABLE_DATA';
export const REGISTER_DRAGGABLE = 'REGISTER_DRAGGABLE';
export const UNREGISTER_DRAGGABLE = 'UNREGISTER_DRAGGABLE';
export const REGISTER_ON_DROP = 'REGISTER_ON_DROP';

export const registerDroppable = (id: string, node: HTMLElement) => ({
  type: REGISTER_DROPPABLE,
  id,
  node,
});

export const unregisterDroppable = (id: string) => ({
  type: UNREGISTER_DROPPABLE,
  id,
});

export const setDroppableData = (id: string, data: any) => ({
  type: SET_DROPPABLE_DATA,
  id,
  data,
});

export const registerDraggable = (id: string) => ({
  type: REGISTER_DRAGGABLE,
  id,
});

export const unregisterDraggable = (id: string) => ({
  type: UNREGISTER_DRAGGABLE,
  id,
});

export const registerOnDrop = (onDrop: (draggableId: string, droppableId: string) => void) => ({
  type: REGISTER_ON_DROP,
  onDrop,
});
