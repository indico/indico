// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import PropTypes from 'prop-types';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

export default function Comment({user, createdDt, modifiedDt, html}) {
  return (
    <div className="i-timeline-item">
      <UserAvatar user={user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box header-indicator-left">
          <div className="i-box-header flexrow">
            <div className="f-self-stretch">
              <Translate>
                <Param name="userName" value={user.fullName} wrapper={<strong />} /> left a comment
              </Translate>{' '}
              <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(createdDt, 'LL')}
              </time>
              {modifiedDt && (
                <span
                  className="review-comment-edited"
                  title={Translate.string('On {modificationDate}', {
                    modificationDate: serializeDate(modifiedDt, 'LL'),
                  })}
                >
                  {' '}
                  · <Translate>edited</Translate>
                </span>
              )}
            </div>
          </div>
          <div className="i-box-content js-form-container">
            <div className="markdown-text" dangerouslySetInnerHTML={{__html: html}} />
          </div>
        </div>
      </div>
    </div>
  );
}

Comment.propTypes = {
  createdDt: PropTypes.string.isRequired,
  html: PropTypes.string.isRequired,
  user: PropTypes.shape({
    fullName: PropTypes.string.isRequired,
    avatarBgColor: PropTypes.string.isRequired,
  }).isRequired,
  modifiedDt: PropTypes.string,
};

Comment.defaultProps = {
  modifiedDt: null,
};
