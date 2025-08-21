// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import {updateState} from './util';

/**
 * Changes the color of the selected Break block
 * @param {object} state State of the timetable
 * @param {object} color New color
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const changeBreakColor = (state, color) => {
  const {selectedId, blocks} = state;
  const selectedBlock = blocks.find(b => b.id === selectedId);
  return updateState(
    state,
    (_.isNumber(selectedBlock.sessionId)
      ? blocks.filter(b => b.sessionId === selectedBlock.sessionId)
      : [selectedBlock]
    ).map(({id}) => ({id, color}))
  );
};

/**
 * Changes the color of the selected block (of type session or break)
 * @param {object} state State of the timetable
 * @param {object} color New color
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const changeSessionColor = (sessions, sessionId, color) => {
  const newSessions = new Map(sessions);
  return newSessions.set(sessionId, {...sessions.get(sessionId), color});
};
