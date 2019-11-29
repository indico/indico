// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getDownloadURL from 'indico-url:event_editing.revision_files_export';

import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import moment from 'moment';
import PropTypes from 'prop-types';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import RevisionLog from './RevisionLog';
import ReviewForm from './ReviewForm';
import {blockPropTypes} from './util';
import {getDetails, getLastTimelineBlock, getLastState, getStaticData} from '../../selectors';
import FileDisplay from '../FileDisplay';

export default function TimelineItem({block}) {
  const {submitter, createdDt} = block;
  const lastBlock = useSelector(getLastTimelineBlock);
  const lastState = useSelector(getLastState);
  const {canComment} = useSelector(getDetails);
  const {fileTypes, eventId, contributionId, editableType} = useSelector(getStaticData);
  const isLastBlock = lastBlock.id === block.id;
  const [visible, setVisible] = useState(isLastBlock);
  const headerOnly = !visible || (!isLastBlock && block.items.length === 0 && !block.comment);

  return (
    <>
      <div className="i-timeline">
        <div className="i-timeline-item">
          <UserAvatar user={block.submitter} />
          <div
            className={`i-timeline-item-box header-indicator-left ${
              headerOnly ? 'header-only' : ''
            }`}
            id={`block-info-${block.id}`}
          >
            <div className="i-box-header flexrow">
              <div className="f-self-stretch">
                {block.header ? (
                  <strong>{block.header}</strong>
                ) : (
                  <Translate>
                    <Param name="submitterName" value={submitter.fullName} wrapper={<strong />} />{' '}
                    submitted revision <Param name="revisionNumber" value={`#${block.number}`} />{' '}
                  </Translate>
                )}
                <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                  {serializeDate(createdDt, 'LL')}
                </time>
              </div>
              {!isLastBlock && (
                <a className="block-info-link i-link" onClick={() => setVisible(!visible)}>
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
                <FileDisplay
                  fileTypes={fileTypes}
                  files={block.files}
                  downloadURL={getDownloadURL({
                    revision_id: block.id,
                    confId: eventId,
                    contrib_id: contributionId,
                    type: editableType,
                  })}
                />
                {block.comment && (
                  <>
                    <div className="titled-rule">
                      <Translate>Comment</Translate>
                    </div>
                    <div dangerouslySetInnerHTML={{__html: block.commentHtml}} />
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      {visible && (
        <RevisionLog items={block.items} separator={isLastBlock}>
          {isLastBlock && !['accepted', 'rejected'].includes(lastState.name) && canComment && (
            <ReviewForm block={block} />
          )}
        </RevisionLog>
      )}
    </>
  );
}

TimelineItem.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
};
