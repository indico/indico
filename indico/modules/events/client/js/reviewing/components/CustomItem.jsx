// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import PropTypes from 'prop-types';

import {serializeDate} from 'indico/utils/date';

import StateIndicator from './StateIndicator';
import UserAvatar from './UserAvatar';

export default function CustomItem({header, user, createdDt, html, state}) {
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
              <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(createdDt, 'LL')}
              </time>
            </div>
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
  createdDt: PropTypes.string.isRequired,
  html: PropTypes.string,
  state: PropTypes.string,
  header: PropTypes.string.isRequired,
  user: PropTypes.shape({
    fullName: PropTypes.string.isRequired,
    avatarBgColor: PropTypes.string.isRequired,
  }).isRequired,
};

CustomItem.defaultProps = {
  html: null,
  state: null,
};
