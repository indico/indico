// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {serializeDate} from 'indico/utils/date';

import ResetReview from './ResetReview';
import * as selectors from './selectors';
import StateIndicator from './StateIndicator';
import {blockItemPropTypes} from './util';

export default function CustomItem({item: {header, user, reviewedDt, html, revisionId}, state}) {
  const lastRevertableRevisionId = useSelector(selectors.getLastRevertableRevisionId);

  return (
    <div className="i-timeline-item">
      <UserAvatar user={user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box">
          <div
            className={`i-box-header flexrow ${!html ? 'header-only' : ''}`}
            style={{alignItems: 'center'}}
          >
            <div className="f-self-stretch">
              {header}{' '}
              <time dateTime={serializeDate(reviewedDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}>
                {serializeDate(reviewedDt, 'LL')}
              </time>
            </div>
            {revisionId === lastRevertableRevisionId && <ResetReview revisionId={revisionId} />}
            {state && <StateIndicator state={state} circular />}
          </div>
          {html && (
            <div className="i-box-content js-form-container">
              <div className="markdown-text" dangerouslySetInnerHTML={{__html: html}} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

CustomItem.propTypes = {
  item: PropTypes.shape(blockItemPropTypes).isRequired,
  state: PropTypes.string,
};

CustomItem.defaultProps = {
  state: null,
};
