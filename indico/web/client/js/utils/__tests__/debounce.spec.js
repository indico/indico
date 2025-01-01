// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {makeAsyncDebounce} from '../debounce';

jest.useFakeTimers();

describe('Debounce', () => {
  it('works', async () => {
    const debounce = makeAsyncDebounce(500);

    const spy = jest.fn();
    const fn = jest.fn(val => {
      return new Promise(resolve =>
        setTimeout(() => {
          resolve(val);
          spy();
        }, 10)
      );
    });

    const caller = val => debounce(() => fn(val));

    const promises = [];
    promises.push(caller(1));
    jest.advanceTimersByTime(400);
    promises.push(caller(2));
    jest.advanceTimersByTime(400);
    promises.push(caller(3));
    jest.advanceTimersByTime(400);
    expect(spy).not.toHaveBeenCalled();
    jest.advanceTimersByTime(110);
    expect(spy).toHaveBeenCalledTimes(1);
    await expect(Promise.all(promises)).resolves.toEqual([3, 3, 3]);

    expect(fn).toHaveBeenCalledTimes(1);
  });
});
