// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {FinalRevisionState} from '../../models';

import CommentItem from './CommentItem';
import CustomItem from './CustomItem';
import {blockItemPropTypes} from './util';

export default function RevisionLog({items, state, children, separator}) {
  return (
    <div className="i-timeline">
      <div className="i-timeline with-line">
        <div className="i-timeline-connect-up" />
        {items.map(item => {
          if (item.custom) {
            return <CustomItem key={item.id} item={item} state={state} />;
          }
          return <CommentItem key={item.id} {...item} />;
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
  items: PropTypes.arrayOf(PropTypes.shape(blockItemPropTypes)).isRequired,
  state: PropTypes.oneOf(Object.values(FinalRevisionState)),
  children: PropTypes.node,
  separator: PropTypes.bool,
};

RevisionLog.defaultProps = {
  children: null,
  separator: false,
  state: null,
};
