// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export function toClasses(...params) {
  const obj = params.length === 1 ? params[0] : params;
  if (Array.isArray(obj)) {
    return obj.join(' ').trim();
  } else if (typeof obj === 'string') {
    return obj;
  }
  return Object.entries(obj)
    .map(([k, v]) => (v ? ` ${k}` : ''))
    .join('')
    .trim();
}
