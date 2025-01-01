// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import CommentItem from './CommentItem';
import {blockItemPropTypes} from './util';

export default function RevisionLog({items, children, separator}) {
  return (
    <div className="i-timeline">
      <div className="i-timeline with-line">
        <div className="i-timeline-connect-up" />
        {items.map(item => (
          <CommentItem key={item.id} {...item} />
        ))}
        {children}
      </div>
      {separator && (
        <>
          <div className="i-timeline to-separator-wrapper">
            <div className="i-timeline-connect-down to-separator" />
          </div>
          <div className="i-timeline-separator" />
        </>
      )}
    </div>
  );
}

RevisionLog.propTypes = {
  items: PropTypes.arrayOf(PropTypes.shape(blockItemPropTypes)).isRequired,
  children: PropTypes.node,
  separator: PropTypes.bool,
};

RevisionLog.defaultProps = {
  children: null,
  separator: false,
};
