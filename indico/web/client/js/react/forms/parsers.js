// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

function number(value) {
  if (typeof value === 'number') {
    return value;
  } else if (typeof value === 'string') {
    if (value === '') {
      return null;
    } else if (!isNaN(+value)) {
      return +value;
    }
  }
  // keep whatever we have, maybe a validator can make sense of it
  // and show a suitable error
  return value;
}

function nullIfEmpty(value) {
  return value === '' ? null : value;
}

export default {
  number,
  nullIfEmpty,
};
