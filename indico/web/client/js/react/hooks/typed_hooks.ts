// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {AxiosRequestConfig} from 'axios';
import {useState, useCallback, useEffect, useRef, useMemo} from 'react';

import {useIndicoAxios} from 'indico/react/hooks/hooks';

export interface MutateOptions {
  optimistic: boolean;
}

export type IndicoAxiosOptions = AxiosRequestConfig & {
  camelize: boolean;
  skipCamelize: boolean;
  unhandledErrors: number[];
};

/**
 * A hook that provides a declarative way to make an HTTP request with Axios and a `mutate` method
 * that can be used to preemptively update the frontend while a request to the backend is still
 * pending.
 *
 * @param axiosConfig - the url or an axios config object
 * @param hookConfig - settings for this hook and useAxios
 */
export function useIndicoAxiosWithMutation<T>(
  axiosConfig: AxiosRequestConfig,
  hookConfig: Partial<IndicoAxiosOptions> = {}
) {
  const [patchedData, setPatchedData] = useState<T | null>(null);
  const [mutating, setMutating] = useState(false);
  const [mutationError, setMutationError] = useState<unknown>(null);
  const {
    response,
    data,
    loading: fetching,
    error,
    reFetch,
  } = useIndicoAxios(axiosConfig, hookConfig);
  const patchedDataRef = useRef(patchedData);

  const mutate = useCallback(
    async <R>(
      request: Promise<R>,
      updater: (data: T) => T,
      mutateOptions: Partial<MutateOptions> = {}
    ) => {
      if (mutating) {
        return;
      }
      setMutating(true);
      setMutationError(null);

      const {optimistic = true} = mutateOptions;
      const previous = patchedDataRef.current;

      try {
        if (optimistic) {
          const newData = updater(patchedDataRef.current);
          setPatchedData(newData);
        }

        let result: R;
        try {
          result = await request;
        } catch (e) {
          setMutationError(e);
          if (optimistic) {
            setPatchedData(previous);
          }
          throw e;
        }

        if (!optimistic) {
          const newData = updater(patchedDataRef.current);
          setPatchedData(newData);
        }

        const refetchResult = await reFetch();
        setPatchedData(refetchResult.data);

        return result;
      } finally {
        setMutating(false);
      }
    },
    [reFetch, mutating]
  );

  useEffect(() => {
    setPatchedData(data);
  }, [data]);

  useEffect(() => {
    patchedDataRef.current = patchedData;
  }, [patchedData]);

  return useMemo(
    () => ({
      data: patchedData,
      response,
      loading: fetching && !mutating,
      fetching,
      error,
      reFetch,
      mutate,
      mutating,
      mutationError,
    }),
    [patchedData, response, fetching, error, reFetch, mutate, mutating, mutationError]
  );
}
