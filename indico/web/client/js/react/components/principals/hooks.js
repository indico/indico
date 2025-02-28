// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import principalsURL from 'indico-url:core.principals';
import eventCategoryRolesURL from 'indico-url:event_management.api_category_roles';
import eventRolesURL from 'indico-url:event_management.api_event_roles';
import eventPrincipalsURL from 'indico-url:event_management.api_principals';
import registrationFormsURL from 'indico-url:event_registration.api_registration_forms';

import _ from 'lodash';
import {useState, useEffect} from 'react';

import {useIndicoAxios} from 'indico/react/hooks';

import {PermissionManager} from './util';

/**
 * This hook will fetch information about principals as needed
 * @param {Array} principalIds - list of principal IDs
 * @param {Number} eventId - list of the event id if event-related principals are allowed
 */
export const useFetchPrincipals = (principalIds, eventId = null) => {
  const [informationMap, setInformationMap] = useState({});
  const missingPrincipalIds = _.difference(principalIds, Object.keys(informationMap));

  const {data} = useIndicoAxios(
    {
      url: eventId === null ? principalsURL() : eventPrincipalsURL({event_id: eventId}),
      method: 'POST',
      data: {
        values: missingPrincipalIds,
      },
    },
    {camelize: true, manual: !missingPrincipalIds.length}
  );

  useEffect(() => {
    if (missingPrincipalIds.length && data) {
      setInformationMap(prev => ({...prev, ...data}));
    }
  }, [data, missingPrincipalIds.length]);

  return informationMap;
};

/**
 * This hook will handle fetching information about available permissions from the backend
 * and returning a `PermissionManager` that follows their structure.
 */
export const usePermissionInfo = url => {
  const [loaded, setLoaded] = useState(false);
  const [data, setData] = useState(null);

  const {data: reqData} = useIndicoAxios(url, {camelize: true});

  if (!loaded && reqData) {
    setData({...reqData});
    setLoaded(true);
  }

  return [loaded ? new PermissionManager(data.tree, data.default) : null, data];
};

/**
 * PermissionInfoProvider can be used to get the permissionInfo
 * in a class-based component.
 *
 * Do not use this for new components; write them as functional
 * components instead!
 */
export const PermissionInfoProvider = ({url, children}) => {
  const [permissionManager, permissionInfo] = usePermissionInfo(url);
  return children(permissionManager, permissionInfo);
};

const _useFetchPrincipalList = (eventId, enabled, urlFunc, options = {}) => {
  const {data, loading} = useIndicoAxios(urlFunc({event_id: eventId}), {
    manual: !enabled || eventId === null,
    camelize: true,
    ...options,
  });

  return [data || [], loading];
};

/**
 * This hook fetches the list of selectable principals available for a given event.
 * If the `eventId` is null or a principal type is disabled, nothing is fetched.
 */
export const useFetchAvailablePrincipals = ({
  eventId,
  withEventRoles,
  withCategoryRoles,
  withRegistrants,
}) => {
  const [eventRoles, loadingEventRoles] = _useFetchPrincipalList(
    eventId,
    withEventRoles,
    eventRolesURL
  );
  const [categoryRoles, loadingCategoryRoles] = _useFetchPrincipalList(
    eventId,
    withCategoryRoles,
    eventCategoryRolesURL
  );
  const [registrationForms, loadingRegistrationForms] = _useFetchPrincipalList(
    eventId,
    withRegistrants,
    registrationFormsURL,
    {unhandledErrors: [404]} // feature may be disabled
  );
  const loading = loadingEventRoles || loadingCategoryRoles || loadingRegistrationForms;
  return {eventRoles, categoryRoles, registrationForms, loading};
};
