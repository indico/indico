// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useSelector} from 'react-redux';

import * as selectors from './selectors';
import {entrySchema, isChildOf} from './util';

import './Entry.module.scss';

export default function Entry({event: entry}) {
  const {title, slotTitle, code} = entry;
  const contributions = useSelector(selectors.getChildren);
  const displayMode = useSelector(selectors.getDisplayMode);
  const hasContribs = contributions.some(c => isChildOf(c, entry));

  return (
    <>
      {displayMode === 'compact' && hasContribs && <div styleName="compact-title">{title}</div>}
      <div styleName="entry-title">
        {(displayMode === 'full' || !hasContribs) && [
          title,
          slotTitle && `: ${slotTitle}`,
          code && ` (${code})`,
        ]}
      </div>
    </>
  );
}

Entry.propTypes = {
  event: entrySchema.isRequired,
};
