import {MousePosition, Rect} from './types';

export function pointerInside(pointer: MousePosition, rect: Rect) {
  return (
    pointer.x > rect.left &&
    pointer.x < rect.left + rect.width &&
    pointer.y > rect.top &&
    pointer.y < rect.top + rect.height
  );
}
