// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {useCallback, useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import * as actions from './actions';
import {POSTER_BLOCK_CONTRIBUTIONS_MODAL, useModal} from './ModalContext';
import * as selectors from './selectors';
import {BlockEntry, EntryType, Navigation, SessionBlockId} from './types';
import {createTimetableURL, parseTimetableURL} from './utils';

export function NavigationController() {
  const dispatch = useDispatch();
  const eventId = useSelector(selectors.getEventId);
  const currentDate = useSelector(selectors.getCurrentDate);
  const eventEndDt = useSelector(selectors.getEventEndDt);
  const eventStartDt = useSelector(selectors.getEventStartDt);
  const entries = useSelector(selectors.getEntries);
  const sessions = useSelector(selectors.getSessions);
  const {openModal} = useModal();

  const isPosterSessionBlock = useCallback(
    (blockId: SessionBlockId) => {
      const block = entries.entries[blockId] as BlockEntry;
      return sessions[block.sessionId]?.isPoster ?? false;
    },
    [entries, sessions]
  );

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
      const expandedSessionBlockIsPoster =
        location.expandedSessionBlockId && isPosterSessionBlock(location.expandedSessionBlockId);
      dispatch(actions.setCurrentDate(location.currentDate, eventId, false));
      if (!expandedSessionBlockIsPoster) {
        dispatch(actions.setExpandedSessionBlock(location.expandedSessionBlockId, eventId, false));
      } else {
        dispatch(actions.setExpandedSessionBlock(null, eventId, false));
        openModal(POSTER_BLOCK_CONTRIBUTIONS_MODAL, {id: location.expandedSessionBlockId!});
      }
      if (replaceState) {
        window.history.replaceState(
          null,
          '',
          createTimetableURL(
            eventId,
            location.currentDate,
            expandedSessionBlockIsPoster ? null : location.expandedSessionBlockId
          )
        );
      }
    }

    function popStateHandler() {
      const location = parseTimetableURL(document.location.pathname);
      if (location === null) {
        return;
      }
      const validatedLocation = getValidatedLocation(location);
      navigate(validatedLocation, true);
    }

    function loadHandler() {
      const location = parseTimetableURL(document.location.pathname);
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
  }, [dispatch, currentDate, eventId, getValidatedLocation, isPosterSessionBlock, openModal]);

  return null;
}
