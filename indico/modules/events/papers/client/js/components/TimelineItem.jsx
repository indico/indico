// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React, {useState} from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import {useSelector} from 'react-redux';
import {Transition} from 'semantic-ui-react';

import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import PaperReviewForm from './PaperReviewForm';
import RevisionJudgment from './RevisionJudgment';
import RevisionTimeline from './RevisionTimeline';
import SubmitRevision from './SubmitRevision';
import UserAvatar from './UserAvatar';
import {canCommentPaper, canReviewPaper, getPaperDetails} from '../selectors';

export default function TimelineItem({revision}) {
  const {submitter, isLastRevision, number, submittedDt, files, timeline} = revision;
  const submitterName = submitter.isSystem ? Translate.string('A user') : submitter.fullName;
  const {isInFinalState} = useSelector(getPaperDetails);
  const canComment = useSelector(canCommentPaper);
  const canReview = useSelector(canReviewPaper);
  const [visible, setVisible] = useState(false);

  return (
    <>
      <div className="i-timeline">
        <div className="i-timeline-item">
          <UserAvatar user={submitter} />
          <div
            className={`i-timeline-item-box header-indicator-left ${
              !isLastRevision && !visible ? 'header-only' : ''
            }`}
            id={`revision-info-${revision.id}`}
          >
            <div className="i-box-header flexrow">
              <div className="f-self-stretch">
                <Translate>
                  <Param name="submitterName" value={submitterName} wrapper={<strong />} />{' '}
                  submitted paper revision <Param name="revisionNumber" value={`#${number}`} />{' '}
                </Translate>
                <time dateTime={serializeDate(submittedDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                  {serializeDate(submittedDt, 'LL')}
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
            <Transition.Group animation="slide down" duration={200}>
              {(visible || isLastRevision) && (
                <div
                  className={`i-box-content submission-info ${
                    !isLastRevision ? 'weak-hidden' : ''
                  }`}
                >
                  <ul className="file-list">
                    {_.sortBy(files, 'filename').map(file => (
                      <li className="truncate-text" key={file.id}>
                        <a
                          href={file.downloadURL}
                          className={`attachment ${file.icon}`}
                          title={file.filename}
                        >
                          {' '}
                          <span className="title">{file.filename}</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Transition.Group>
          </div>
        </div>
      </div>
      <Transition.Group animation="slide down" duration={200}>
        {(visible || isLastRevision) && (
          <div className={`i-timeline ${!isLastRevision ? 'weak-hidden' : ''}`}>
            {(timeline.length > 0 || canReview || canComment) && (
              <RevisionTimeline revision={revision} />
            )}
            {isLastRevision && (
              <>
                {(canComment || canReview) && <PaperReviewForm />}
                <div className="i-timeline to-separator-wrapper">
                  <div className="i-timeline-connect-down to-separator" />
                </div>
                <div className="i-timeline-separator" />
                <SubmitRevision />
                {isInFinalState && <RevisionJudgment revision={revision} />}
              </>
            )}
          </div>
        )}
      </Transition.Group>
    </>
  );
}

TimelineItem.propTypes = {
  revision: PropTypes.object.isRequired,
};
