import {MutableRefObject} from 'react';

interface Coords {
  x: number;
  y: number;
}

export type MousePosition = Coords;
export type Transform = Coords;

export interface Rect {
  top: number;
  left: number;
  bottom: number;
  right: number;
  width: number;
  height: number;
}

export type DragState = 'idle' | 'mousedown' | 'dragging';

export interface Over {
  id: string;
  rect: Rect;
}

export type HTMLRef = MutableRefObject<HTMLElement | null>;

export interface Droppable {
  node: HTMLRef;
}

export interface Draggable {
  node: HTMLRef;
}

export interface DraggableData {
  rect?: Rect;
  transform?: {x: number; y: number};
}

export interface DragEvent {
  who: string;
  over: Over[];
  delta: Transform;
  mouse: MousePosition;
}
export type OnDrop = (who: string, over: Over[], delta: Transform, mouse: MousePosition) => void;

export type Modifier = ({
  draggingNodeRect,
  transform,
}: {
  draggingNodeRect: Rect;
  transform: Transform;
}) => Transform;
