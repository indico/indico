// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {MousePosition, Rect} from './types';

export function pointerInside(pointer: MousePosition, rect: Rect) {
  return (
    pointer.x > rect.left &&
    pointer.x < rect.left + rect.width &&
    pointer.y > rect.top &&
    pointer.y < rect.top + rect.height
  );
}
