// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export function formatDate(formatString, date) {
  if (!date) {
    return '';
  }

  const year = `${date.getFullYear()}`;
  const month = `${date.getMonth() + 1}`;
  const day = `${date.getDate()}`;

  return formatString
    .replace(/yy+/i, s => {
      if (s.length === 2) {
        return year.slice(3);
      }
      return year;
    })
    .replace(/m{1,2}/i, s => month.padStart(s.length, '0'))
    .replace(/d{1,2}/i, s => day.padStart(s.length, '0'));
}

export const ISO_FORMAT = 'yyyy-mm-dd';
