// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import moment from 'moment';
import PropTypes from 'prop-types';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import ChangesConfirmation from './ChangesConfirmation';
import RevisionLog from './RevisionLog';
import ReviewForm from './ReviewForm';
import {blockPropTypes} from './util';
import * as selectors from './selectors';
import FileDisplay from './FileDisplay';
import StateIndicator from './StateIndicator';

import './TimelineItem.module.scss';

export default function TimelineItem({block}) {
  const {submitter, createdDt} = block;
  const lastBlock = useSelector(selectors.getLastTimelineBlock);
  const needsSubmitterConfirmation = useSelector(selectors.needsSubmitterConfirmation);
  const canPerformSubmitterActions = useSelector(selectors.canPerformSubmitterActions);
  const {canComment, state: editableState} = useSelector(selectors.getDetails);
  const {fileTypes} = useSelector(selectors.getStaticData);
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
                    submitted revision <Param name="revisionNumber" value={`#${block.number}`} />
                  </Translate>
                )}{' '}
                <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                  {serializeDate(createdDt, 'LL')}
                </time>
              </div>
              {!isLastBlock && (
                <>
                  <a className="block-info-link i-link" onClick={() => setVisible(!visible)}>
                    {visible ? (
                      <Translate>Hide old revision</Translate>
                    ) : (
                      <Translate>Show old revision</Translate>
                    )}
                  </a>
                  {!visible && block.finalState && (
                    <div styleName="state-indicator">
                      <StateIndicator state={block.finalState.name} circular />
                    </div>
                  )}
                </>
              )}
            </div>
            {visible && (
              <div className="i-box-content">
                <FileDisplay
                  fileTypes={fileTypes}
                  files={block.files}
                  downloadURL={block.downloadFilesURL}
                  tags={block.tags}
                />
                {canPerformSubmitterActions && needsSubmitterConfirmation && isLastBlock && (
                  <ChangesConfirmation />
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      {visible && (
        <RevisionLog items={block.items} separator={isLastBlock}>
          {isLastBlock && !['accepted', 'rejected'].includes(editableState.name) && canComment && (
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
