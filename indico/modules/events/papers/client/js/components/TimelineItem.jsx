// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
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

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import PaperReviewForm from './PaperReviewForm';
import RevisionJudgment from './RevisionJudgment';
import RevisionTimeline from './RevisionTimeline';
import SubmitRevision from './SubmitRevision';
import {canCommentPaper, canReviewPaper, getPaperDetails} from '../selectors';

export default function TimelineItem({block}) {
  const {submitter, isLastRevision, number, submittedDt, files, timeline} = block;
  const submitterName = submitter.isSystem ? Translate.string('A user') : submitter.fullName;
  const canComment = useSelector(canCommentPaper);
  const canReview = useSelector(canReviewPaper);
  const paper = useSelector(getPaperDetails);
  const [visible, setVisible] = useState(isLastRevision);

  return (
    <>
      <div className="i-timeline">
        <div className="i-timeline-item">
          <UserAvatar user={submitter} />
          <div
            className={`i-timeline-item-box header-indicator-left ${!visible ? 'header-only' : ''}`}
            id={`block-info-${block.id}`}
          >
            <div className="i-box-header flexrow">
              <div className="f-self-stretch">
                <Translate>
                  <Param name="submitterName" value={submitterName} wrapper={<strong />} />{' '}
                  submitted paper revision <Param name="revisionNumber" value={`#${number}`} />
                </Translate>{' '}
                <time dateTime={serializeDate(submittedDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                  {serializeDate(submittedDt, 'LL')}
                </time>
              </div>
              {!isLastRevision && (
                <a className="block-info-link i-link" onClick={() => setVisible(!visible)}>
                  {visible ? (
                    <Translate>Hide old revision</Translate>
                  ) : (
                    <Translate>Show old revision</Translate>
                  )}
                </a>
              )}
            </div>
            <Transition animation="slide down" duration={50} visible={visible || isLastRevision}>
              <div className="i-box-content submission-info">
                <ul className="file-list">
                  {_.sortBy(files, 'filename').map(file => (
                    <li className="truncate-text" key={file.id}>
                      <a href={file.downloadURL} className={`attachment ${file.icon}`}>
                        {' '}
                        <span className="title">{file.filename}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </Transition>
          </div>
        </div>
      </div>
      <Transition animation="slide down" duration={50} visible={visible || isLastRevision}>
        <div className="i-timeline" style={{zIndex: isLastRevision ? 1 : 0}}>
          {(timeline.length > 0 || (!paper.isInFinalState && canReview) || canComment) && (
            <div className="i-timeline with-line">
              <div className="i-timeline-connect-up" />
              <RevisionTimeline revision={block} />
              {isLastRevision && (canComment || canReview) && <PaperReviewForm />}
            </div>
          )}
          {isLastRevision && (
            <>
              <div className="i-timeline to-separator-wrapper">
                <div className="i-timeline-connect-down to-separator" />
              </div>
              <div className="i-timeline-separator" />
              <SubmitRevision />
              {paper.isInFinalState && <RevisionJudgment revision={block} />}
            </>
          )}
        </div>
      </Transition>
    </>
  );
}

TimelineItem.propTypes = {
  block: PropTypes.object.isRequired,
};
