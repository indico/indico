// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';

import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import UserAvatar from './UserAvatar';
import StateIndicator from './StateIndicator';

function Comment({comment}) {
  return (
    <div className="i-timeline-item">
      <UserAvatar user={comment.user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box header-indicator-left">
          <div className="i-box-header flexrow">
            <div className="f-self-stretch">
              <Translate>
                <Param name="userName" value={comment.user.fullName} wrapper={<strong />} /> left a
                comment
              </Translate>{' '}
              <time dateTime={serializeDate(comment.createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(comment.createdDt, 'LL')}
              </time>
              {comment.modifiedDt && (
                <span
                  className="review-comment-edited"
                  title={Translate.string('On {modificationDate}', {
                    modificationDate: serializeDate(comment.modifiedDt, 'LL'),
                  })}
                >
                  {' '}
                  · <Translate>edited</Translate>
                </span>
              )}
            </div>
          </div>
          <div className="i-box-content js-form-container">
            <div className="markdown-text" dangerouslySetInnerHTML={{__html: comment.html}} />
          </div>
        </div>
      </div>
    </div>
  );
}

const baseItemPropType = {
  createdDt: PropTypes.string.isRequired,
  html: PropTypes.string.isRequired,
  user: PropTypes.shape({
    fullName: PropTypes.string.isRequired,
    avatarBgColor: PropTypes.string.isRequired,
  }).isRequired,
};

const CommentPropType = PropTypes.shape({
  ...baseItemPropType,
  modifiedDt: PropTypes.string,
});

const CommentPropTypes = {
  comment: CommentPropType.isRequired,
};

Comment.propTypes = CommentPropTypes;

function CustomItem({item}) {
  return (
    <div className="i-timeline-item">
      <UserAvatar user={item.user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box">
          <div
            className={`${item.html ? 'i-box-header' : ''} flexrow`}
            style={{alignItems: 'center'}}
          >
            <div className="f-self-stretch">
              {item.header}{' '}
              <time dateTime={serializeDate(item.createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(item.createdDt, 'LL')}
              </time>
            </div>
            {item.state && <StateIndicator state={item.state} circular />}
          </div>
          {item.html && (
            <div className="i-box-content js-form-container">
              <div className="markdown-text" dangerouslySetInnerHTML={{__html: item.html}} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const CustomItemPropType = PropTypes.shape({
  ...baseItemPropType,
  header: PropTypes.string.isRequired,
});

CustomItem.propTypes = {
  item: CustomItemPropType.isRequired,
};

export default function RevisionItems({items, children, separator}) {
  return (
    <div className="i-timeline">
      <div className="i-timeline with-line">
        <div className="i-timeline-connect-up" />
        {items.map(item => {
          const Component = item.custom ? CustomItem : Comment;
          const props = {[item.custom ? 'item' : 'comment']: item};
          return <Component key={item.id} {...props} />;
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

RevisionItems.propTypes = {
  items: PropTypes.arrayOf(PropTypes.oneOfType([CommentPropType, CustomItemPropType])).isRequired,
  children: PropTypes.node,
  separator: PropTypes.bool,
};

RevisionItems.defaultProps = {
  children: null,
  separator: false,
};
