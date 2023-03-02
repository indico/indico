// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {useSelector} from 'react-redux';
import {Icon, Message} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {FinalRevisionState} from '../../models';

import ChangesConfirmation from './ChangesConfirmation';
import CustomActions from './CustomActions';
import FileDisplay from './FileDisplay';
import ReviewForm from './ReviewForm';
import RevisionLog from './RevisionLog';
import * as selectors from './selectors';
import StateIndicator from './StateIndicator';
import {blockPropTypes, isRequestChangesWithFiles} from './util';

import '../../../styles/timeline.module.scss';
import './TimelineItem.module.scss';

export default function TimelineItem({block, index}) {
  const {submitter, createdDt} = block;
  const timelineBlocks = useSelector(selectors.getTimelineBlocks);
  const validTimelineBlocks = useSelector(selectors.getValidTimelineBlocks);
  const needsSubmitterConfirmation = useSelector(selectors.needsSubmitterConfirmation);
  const canPerformSubmitterActions = useSelector(selectors.canPerformSubmitterActions);
  const {canComment, state: editableState} = useSelector(selectors.getDetails);
  const {fileTypes} = useSelector(selectors.getStaticData);
  const isLastBlock = timelineBlocks[timelineBlocks.length - 1].id === block.id;
  const isLastValidBlock = validTimelineBlocks[validTimelineBlocks.length - 1].id === block.id;
  const isVisibleByDefault =
    isLastValidBlock ||
    (validTimelineBlocks.length >= 2 &&
      validTimelineBlocks[validTimelineBlocks.length - 2].id === block.id &&
      (isRequestChangesWithFiles(
        validTimelineBlocks[validTimelineBlocks.length - 1],
        validTimelineBlocks[validTimelineBlocks.length - 2]
      ) ||
        needsSubmitterConfirmation));
  const [visible, setVisible] = useState(isVisibleByDefault);
  const isUndone = block.finalState.name === FinalRevisionState.undone;

  useEffect(() => {
    // when undoing a judgment deletes the last revision this revision may become the
    // latest one, and thus needs to be unhidden if it had been collapsed before.
    if (isLastValidBlock && isVisibleByDefault && !visible) {
      setVisible(true);
    }
  }, [isLastValidBlock, isVisibleByDefault, visible]);

  return (
    <>
      <div className="i-timeline">
        <div className="i-timeline-item" styleName={isUndone ? 'undone-item' : undefined}>
          <UserAvatar user={block.submitter} />
          <div
            className={`i-timeline-item-box header-indicator-left ${!visible ? 'header-only' : ''}`}
            id={`block-info-${block.id}`}
          >
            <div className="i-box-header flexrow">
              <div className="f-self-stretch" styleName="item-header">
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
                </time>{' '}
                {isUndone && (
                  <Translate as="span" styleName="undone-indicator">
                    Retracted
                  </Translate>
                )}
              </div>
              {!isLastValidBlock && (
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
                {isUndone && (
                  <Message warning>
                    <Icon name="warning sign" />
                    <Translate>This revision has been retracted by the editor.</Translate>
                  </Message>
                )}
                <FileDisplay
                  fileTypes={fileTypes}
                  files={block.files}
                  downloadURL={block.downloadFilesURL}
                  tags={block.tags}
                />
                {canPerformSubmitterActions && needsSubmitterConfirmation && isLastValidBlock && (
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
          {isLastValidBlock &&
            !['accepted', 'rejected'].includes(editableState.name) &&
            canComment && <ReviewForm block={block} />}
        </RevisionLog>
      )}
    </>
  );
}

TimelineItem.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
  index: PropTypes.number.isRequired,
};
