// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {useCallback, useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import * as actions from './actions';
import * as selectors from './selectors';
import {EntryType, Navigation} from './types';
import {createTimetableURL, parseTimetableURL} from './utils';

export function NavigationController() {
  const dispatch = useDispatch();
  const eventId = useSelector(selectors.getEventId);
  const currentDate = useSelector(selectors.getCurrentDate);
  const eventEndDt = useSelector(selectors.getEventEndDt);
  const eventStartDt = useSelector(selectors.getEventStartDt);
  const entries = useSelector(selectors.getEntries);

  const getValidatedLocation = useCallback(
    (location: Partial<Navigation>): Navigation => {
      let newDate = location.currentDate;
      let newExpandedSessionBlockId = location.expandedSessionBlockId ?? undefined;

      if (newDate === undefined) {
        newDate = currentDate;
      } else if (newDate.isAfter(eventEndDt)) {
        newDate = eventEndDt.clone().startOf('day');
      } else if (newDate.isBefore(eventStartDt)) {
        newDate = eventStartDt.clone().startOf('day');
      }

      if (newExpandedSessionBlockId !== undefined) {
        if (
          entries.entries[newExpandedSessionBlockId] === undefined ||
          entries.entries[newExpandedSessionBlockId].type !== EntryType.SessionBlock ||
          !entries.entries[newExpandedSessionBlockId].startDt.isSame(newDate, 'day')
        ) {
          newExpandedSessionBlockId = undefined;
        }
      }

      return {
        currentDate: newDate,
        isExpanded: newExpandedSessionBlockId !== undefined,
        expandedSessionBlockId: newExpandedSessionBlockId ?? null,
      };
    },
    [currentDate, eventStartDt, eventEndDt, entries.entries]
  );

  useEffect(() => {
    function navigate(location: Navigation, replaceState: boolean) {
      dispatch(actions.setCurrentDate(location.currentDate, eventId, false));
      dispatch(actions.setExpandedSessionBlock(location.expandedSessionBlockId, eventId, false));
      if (replaceState) {
        window.history.replaceState(
          null,
          '',
          createTimetableURL(eventId, location.currentDate, location.expandedSessionBlockId)
        );
      }
    }

    function popStateHandler() {
      const location = parseTimetableURL(eventId, document.location.pathname);
      if (location === null) {
        return;
      }
      const validatedLocation = getValidatedLocation(location);
      navigate(validatedLocation, true);
    }

    function loadHandler() {
      const location = parseTimetableURL(eventId, document.location.pathname);
      if (location === null) {
        // We should always include the current date in the URL
        window.history.replaceState(null, '', createTimetableURL(eventId, currentDate));
      } else {
        const validatedLocation = getValidatedLocation(location);
        navigate(validatedLocation, true);
      }
    }

    window.addEventListener('popstate', popStateHandler);
    window.addEventListener('load', loadHandler);

    return () => {
      window.removeEventListener('popstate', popStateHandler);
      window.removeEventListener('load', loadHandler);
    };
  }, [dispatch, currentDate, eventId, getValidatedLocation]);

  return null;
}
