// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {useCallback, useEffect, useRef} from 'react';
import {useSelector} from 'react-redux';

import * as actions from './actions';
import {POSTER_BLOCK_CONTRIBUTIONS_MODAL, useModal} from './ModalContext';
import * as selectors from './selectors';
import {BlockEntry, EntryType, Navigation, ReduxState, SessionBlockId} from './types';
import {createTimetableURL, parseTimetableURL, useTimetableDispatch} from './utils';

export function NavigationController() {
  const dispatch = useTimetableDispatch();
  const eventId = useSelector(selectors.getEventId);
  const currentDate = useSelector(selectors.getCurrentDate);
  const eventEndDt = useSelector(selectors.getEventEndDt);
  const eventStartDt = useSelector(selectors.getEventStartDt);
  const entries = useSelector(selectors.getEntries);
  const sessions = useSelector(selectors.getSessions);
  const expandedSessionBlockIdIsPoster = useSelector((state: ReduxState) => {
    const expandedSessionBlockId = selectors.getExpandedSessionBlockId(state);
    if (!expandedSessionBlockId) {
      return null;
    }
    return selectors.isPosterSessionBlock(state, expandedSessionBlockId);
  });
  const prevExpandedSessionBlockIdIsPoster = useRef<boolean | null>(expandedSessionBlockIdIsPoster);
  const {openModal} = useModal();

  const isPosterSessionBlock = useCallback(
    (blockId: SessionBlockId) => {
      const block = entries[blockId] as BlockEntry;
      return sessions[block.sessionId]?.isPoster ?? false;
    },
    [entries, sessions]
  );

  const navigate = useCallback(
    (location: Navigation, replaceState: boolean) => {
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
    },
    [dispatch, eventId, isPosterSessionBlock, openModal]
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
          entries[newExpandedSessionBlockId] === undefined ||
          entries[newExpandedSessionBlockId].type !== EntryType.SessionBlock ||
          !entries[newExpandedSessionBlockId].startDt.isSame(newDate, 'day')
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
    [currentDate, eventStartDt, eventEndDt, entries]
  );

  useEffect(() => {
    if (
      expandedSessionBlockIdIsPoster === true &&
      prevExpandedSessionBlockIdIsPoster.current === false
    ) {
      // The currently expanded session block has just been changed to a poster session
      const location = parseTimetableURL(document.location.pathname);
      if (location !== null) {
        const validatedLocation = getValidatedLocation(location);
        // Delay the navigation so a modal calling onClose() will
        // run first, and only then will this open a poster session
        // modal.
        setTimeout(() => navigate(validatedLocation, true), 0);
      }
    }
    prevExpandedSessionBlockIdIsPoster.current = expandedSessionBlockIdIsPoster;
  }, [expandedSessionBlockIdIsPoster, getValidatedLocation, navigate]);

  useEffect(() => {
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
  }, [currentDate, eventId, getValidatedLocation, navigate]);

  return null;
}
