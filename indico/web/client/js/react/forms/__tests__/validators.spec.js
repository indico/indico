// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

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

describe('datetime validator with bounds', () => {
  const minStartDt = moment('2026-06-01T00:00:00');
  const maxEndDt = moment('2026-06-30T23:59:59');

  it('accepts a value within bounds', () => {
    expect(v.datetime(minStartDt, maxEndDt)('2026-06-15T12:00:00')).toBeUndefined();
  });

  it('accepts a value equal to minStartDt', () => {
    expect(v.datetime(minStartDt, maxEndDt)('2026-06-01T00:00:00')).toBeUndefined();
  });

  it('accepts a value equal to maxEndDt', () => {
    expect(v.datetime(minStartDt, maxEndDt)('2026-06-30T23:59:59')).toBeUndefined();
  });

  it('rejects a value before minStartDt', () => {
    expect(v.datetime(minStartDt, maxEndDt)('2026-05-31T23:59:59')).not.toBeUndefined();
  });

  it('rejects a value after maxEndDt', () => {
    expect(v.datetime(minStartDt, maxEndDt)('2026-07-01T00:00:00')).not.toBeUndefined();
  });

  it('only enforces minStartDt when maxEndDt is not provided', () => {
    expect(v.datetime(minStartDt)('2026-05-31T23:59:59')).not.toBeUndefined();
    expect(v.datetime(minStartDt)('2099-01-01T00:00:00')).toBeUndefined();
  });

  it('only enforces maxEndDt when minStartDt is not provided', () => {
    expect(v.datetime(null, maxEndDt)('2026-07-01T00:00:00')).not.toBeUndefined();
    expect(v.datetime(null, maxEndDt)('2000-01-01T00:00:00')).toBeUndefined();
  });
});
