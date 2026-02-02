// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {renderHook, act} from '@testing-library/react-hooks';
import mockAxios from 'jest-mock-axios';
import _ from 'lodash';

import {indicoAxios} from 'indico/utils/axios';

import {useIndicoAxiosWithMutation} from '../typed_hooks';

describe('useIndixoAxiosWithMutation hook', () => {
  let mockedData;
  const BASE_URL = 'http://nowhere';
  const DELETE_URL = 'http://delete';

  // make useIndicoAxiosWithMutation always return this data
  beforeEach(() => {
    mockedData = {
      1: {
        id: 1,
        title: 'mocked title',
      },
      2: {
        id: 2,
        title: '2nd mocked title',
      },
    };
  });

  afterEach(() => {
    mockAxios.reset();
  });

  it('should return default values', async () => {
    const {result} = renderHook(() => useIndicoAxiosWithMutation({url: BASE_URL}));
    const {data, loading, mutating, mutationError, error} = result.current;

    expect(data).toBe(null);
    expect(loading).toBe(true);
    expect(mutating).toBe(false);
    expect(mutationError).toBe(null);
    expect(error).toBe(null);
  });

  it('should return data', async () => {
    const {result, waitFor} = renderHook(() => useIndicoAxiosWithMutation({url: BASE_URL}));

    act(() => {
      mockAxios.mockResponseFor(BASE_URL, {
        data: mockedData,
      });
    });

    await waitFor(() => result.current.loading === false);
    expect(result.current.data).toEqual(mockedData);
    expect(result.current.error).toEqual(null);
    expect(result.current.mutating).toBe(false);
    expect(result.current.mutationError).toEqual(null);
  });

  it.each([true, false])('should run mutation when optimistic is %j', async optimistic => {
    const {result, waitFor} = renderHook(() => useIndicoAxiosWithMutation({url: BASE_URL}));

    act(() => {
      mockAxios.mockResponseFor(BASE_URL, {
        data: mockedData,
      });
    });

    await waitFor(() => result.current.loading === false);

    await act(async () => {
      const promise = result.current.mutate(
        indicoAxios.delete(DELETE_URL),
        stale => _.omit(stale, 1),
        {optimistic}
      );

      await waitFor(() => mockAxios.getReqByUrl(DELETE_URL) !== undefined);

      expect(result.current.mutating).toBe(true);
      // If updating optimistically, data should be changed before getting a response
      // from the server
      expect(result.current.data).toEqual(optimistic ? _.omit(mockedData, 1) : mockedData);

      mockAxios.mockResponseFor(DELETE_URL, {
        data: {success: true},
      });
      await waitFor(() => mockAxios.getReqByUrl(BASE_URL) !== undefined);
      // If not updating optimistically, data is changed here
      expect(result.current.data).toEqual(_.omit(mockedData, 1));

      mockAxios.mockResponseFor(BASE_URL, {
        data: mockedData,
      });

      await promise;
    });

    await waitFor(() => result.current.mutating === false);

    expect(result.current.fetching).toEqual(false);
    expect(result.current.loading).toEqual(false);
    expect(result.current.data).toEqual(mockedData);
    expect(result.current.error).toEqual(null);
    expect(result.current.mutationError).toEqual(null);
  });

  it('should set mutationError', async () => {
    const {result, waitFor} = renderHook(() => useIndicoAxiosWithMutation({url: BASE_URL}));

    act(() => {
      mockAxios.mockResponseFor(BASE_URL, {
        data: mockedData,
      });
    });

    await waitFor(() => result.current.loading === false);

    await act(async () => {
      const promise = result.current.mutate(indicoAxios.delete(DELETE_URL), stale =>
        _.omit(stale, 1)
      );

      await waitFor(() => mockAxios.getReqByUrl(DELETE_URL) !== undefined);
      mockAxios.mockError();

      expect(result.current.data).toEqual(_.omit(mockedData, 1));

      await expect(promise).rejects.toEqual({isAxiosError: true});
    });

    expect(result.current.data).toEqual(mockedData);
    expect(result.current.mutationError).toEqual({isAxiosError: true});
    expect(result.current.error).toBe(null);
    expect(result.current.loading).toBe(false);
    expect(result.current.fetching).toBe(false);
    expect(result.current.mutating).toBe(false);
  });

  it('should re-throw user error', async () => {
    const {result, waitFor} = renderHook(() => useIndicoAxiosWithMutation({url: BASE_URL}));

    act(() => {
      mockAxios.mockResponseFor(BASE_URL, {
        data: mockedData,
      });
    });

    await waitFor(() => result.current.loading === false);

    await act(async () => {
      const promise = result.current.mutate(indicoAxios.delete(DELETE_URL), () => {
        throw new Error('user error');
      });
      await expect(promise).rejects.toThrow('user error');
    });

    // User error is not a mutation error
    expect(result.current.error).toBe(null);
    expect(result.current.mutationError).toBe(null);
    expect(result.current.loading).toBe(false);
    expect(result.current.fetching).toBe(false);
    expect(result.current.mutating).toBe(false);
  });
});
