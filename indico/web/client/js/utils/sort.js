// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// Same as natural_sort_key
export function natSortCompare(a, b) {
  if (a === b) {
    return 0;
  }

  const numberRegex = /([0-9]+)/;
  const toInt = (v, i) => (i % 2 === 0 ? v : parseInt(v, 10));

  a = a.split(numberRegex).map(toInt);
  b = b.split(numberRegex).map(toInt);

  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    if (a[i] < b[i]) {
      return -1;
    } else if (a[i] > b[i]) {
      return 1;
    }
  }

  return a.length === b.length ? 0 : a.length < b.length ? -1 : 1;
}
