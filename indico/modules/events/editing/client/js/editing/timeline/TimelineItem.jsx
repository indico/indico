// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {useSelector} from 'react-redux';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import ChangesConfirmation from './ChangesConfirmation';
import CustomActions from './CustomActions';
import FileDisplay from './FileDisplay';
import ReviewForm from './ReviewForm';
import RevisionLog from './RevisionLog';
import * as selectors from './selectors';
import StateIndicator from './StateIndicator';
import {blockPropTypes} from './util';

import './TimelineItem.module.scss';

export default function TimelineItem({block, index}) {
  const {submitter, createdDt} = block;
  const lastBlock = useSelector(selectors.getLastTimelineBlock);
  const needsSubmitterConfirmation = useSelector(selectors.needsSubmitterConfirmation);
  const canPerformSubmitterActions = useSelector(selectors.canPerformSubmitterActions);
  const {canComment, state: editableState} = useSelector(selectors.getDetails);
  const {fileTypes} = useSelector(selectors.getStaticData);
  const isLastBlock = lastBlock.id === block.id;
  const [visible, setVisible] = useState(isLastBlock);
  const headerOnly = !visible || (!isLastBlock && block.items.length === 0 && !block.comment);

  useEffect(() => {
    // when undoing a judgment deletes the last revision this revision may become the
    // latest one, and thus needs to be unhidden if it had been collapsed before.
    if (isLastBlock && !visible) {
      setVisible(true);
    }
  }, [isLastBlock, visible]);

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
              <div className="f-self-stretch" styleName="header">
                <span styleName="item-index">#{index + 1}</span>{' '}
                <span>
                  {block.header ? (
                    <strong>{block.header}</strong>
                  ) : (
                    <Translate>
                      <Param name="submitterName" value={submitter.fullName} wrapper={<strong />} />{' '}
                      has submitted files
                    </Translate>
                  )}
                </span>{' '}
                <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}>
                  {serializeDate(createdDt, 'LLL')}
                </time>
              </div>
              {!isLastBlock && (
                <>
                  <a className="block-info-link i-link" onClick={() => setVisible(!visible)}>
                    {visible ? <Translate>Hide</Translate> : <Translate>Show details</Translate>}
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
            {!!block.customActions.length && (
              <CustomActions url={block.customActionURL} actions={block.customActions} />
            )}
          </div>
        </div>
      </div>
      {visible && (
        <RevisionLog items={block.items} state={block.finalState.name} separator={isLastBlock}>
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
  index: PropTypes.number.isRequired,
};
