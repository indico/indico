// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import moment from 'moment';
import PropTypes from 'prop-types';

import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import RevisionComments from './RevisionComments';
import UserAvatar from './UserAvatar';

export default function TimelineItem({revision, isLastRevision}) {
  const {submitter, createdDt} = revision;
  const [visible, setVisible] = useState(false);

  return (
    <>
      <div className="i-timeline">
        <div className="i-timeline-item">
          <UserAvatar user={revision.submitter} />
          <div
            className={`i-timeline-item-box header-indicator-left ${
              !isLastRevision && !visible ? 'header-only' : ''
            }`}
            id={`revision-info-${revision.id}`}
          >
            <div className="i-box-header flexrow">
              <div className="f-self-stretch">
                <Translate>
                  <Param name="submitterName" value={submitter.fullName} wrapper={<strong />} />{' '}
                  submitted revision <Param name="revisionNumber" value={`#${revision.number}`} />{' '}
                </Translate>
                <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                  {serializeDate(createdDt, 'LL')}
                </time>
              </div>
              {!isLastRevision && (
                <a className="revision-info-link i-link" onClick={() => setVisible(!visible)}>
                  {visible ? (
                    <Translate>Hide old revision</Translate>
                  ) : (
                    <Translate>Show old revision</Translate>
                  )}
                </a>
              )}
            </div>
            {visible && (
              <div className="i-box-content">
                {revision.comment && (
                  <>
                    <div className="titled-rule">
                      <Translate>Comment</Translate>
                    </div>
                    <div dangerouslySetInnerHTML={{__html: revision.commentHtml}} />
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      {(visible || isLastRevision) && revision.comments.length !== 0 && (
        <>
          <RevisionComments comments={revision.comments}>
            {isLastRevision && (
              <>
                <div className="i-timeline to-separator-wrapper">
                  <div className="i-timeline-connect-down to-separator" />
                </div>
                <div className="i-timeline-separator" />
              </>
            )}
          </RevisionComments>
        </>
      )}
    </>
  );
}

TimelineItem.propTypes = {
  revision: PropTypes.object.isRequired,
  isLastRevision: PropTypes.bool.isRequired,
};
