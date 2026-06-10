// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import v from '../validators';

describe('datetime validator', () => {
  const datetime = v.datetime();

  it('accepts a full date and time', () => {
    expect(datetime('2026-06-08T10:20:00')).toBeUndefined();
  });

  it('rejects a missing date (cleared date picker)', () => {
    expect(datetime('T10:20:00')).not.toBeUndefined();
  });

  it('rejects a missing time', () => {
    expect(datetime('2026-06-08T')).not.toBeUndefined();
  });

  it('rejects empty and malformed values', () => {
    expect(datetime('')).not.toBeUndefined();
    expect(datetime('T')).not.toBeUndefined();
    expect(datetime('nonsense')).not.toBeUndefined();
  });
});
