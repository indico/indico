// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useSelector} from 'react-redux';

import NewEntryDropdown from './components/NewEntryDropdown';
import * as selectors from './selectors';
import {entrySchema, entryTypes, isChildOf} from './util';

import './Entry.module.scss';

export default function Entry({event: entry}) {
  const {type, title} = entry;
  const contributions = useSelector(selectors.getVisibleChildren);
  const displayMode = useSelector(selectors.getDisplayMode);

  if (type === 'placeholder') {
    return <NewEntryDropdown icon={null} open />;
  }

  const hasContribs = contributions.some(c => isChildOf(c, entry));
  return (
    <>
      {displayMode === 'compact' && hasContribs && <div styleName="compact-title">{title}</div>}
      <div styleName="entry-title">
        {(displayMode !== 'compact' || !hasContribs) && entryTypes[type].formatTitle(entry)}
      </div>
    </>
  );
}

Entry.propTypes = {
  event: entrySchema.isRequired,
};
