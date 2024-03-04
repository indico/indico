// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {timetableData} from './sample-data';

const sessionBlocks = Object.values(timetableData)
  .map(e => Object.values(e))
  .flat();
const contribs = sessionBlocks
  .map(e => (e.entries ? Object.values(e.entries).map(v => ({...v, parent: e.id})) : []))
  .flat();

export default [...sessionBlocks, ...contribs].map(e => ({
  id: e.id,
  title: e.title,
  start: new Date(Date.parse(`${e.startDate.date} ${e.startDate.time}`)),
  end: new Date(Date.parse(`${e.endDate.date} ${e.endDate.time}`)),
  desc: e.description,
  color: {text: e.textColor, background: e.color},
  parent: e.parent,
}));
