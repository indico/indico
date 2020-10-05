// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import CommentItem from './CommentItem';
import CustomItem from './CustomItem';

export default function RevisionLog({items, children, separator}) {
  return (
    <div className="i-timeline">
      <div className="i-timeline with-line">
        <div className="i-timeline-connect-up" />
        {items.map(item => {
          const Component = item.custom ? CustomItem : CommentItem;
          return <Component key={item.id} {...item} />;
        })}
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
  items: PropTypes.array.isRequired,
  children: PropTypes.node,
  separator: PropTypes.bool,
};

RevisionLog.defaultProps = {
  children: null,
  separator: false,
};
