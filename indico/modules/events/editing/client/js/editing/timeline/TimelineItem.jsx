// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import {Divider, Icon, Message} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {RevisionType, RevisionTypeStates} from '../../models';

import ChangesConfirmation from './ChangesConfirmation';
import CustomActions from './CustomActions';
import FileDisplay from './FileDisplay';
import ResetReview from './ResetReview';
import ReviewComment from './ReviewComment';
import ReviewForm from './ReviewForm';
import RevisionLog from './RevisionLog';
import * as selectors from './selectors';
import StateIndicator from './StateIndicator';
import {blockPropTypes, INDICO_BOT_USER} from './util';

import '../../../styles/timeline.module.scss';
import './TimelineItem.module.scss';

export default function TimelineItem({block, index}) {
  const {createdDt, modifiedDt, isUndone} = block;
  const lastTimelineBlock = useSelector(selectors.getLastTimelineBlock);
  const lastValidTimelineBlock = useSelector(selectors.getLastValidTimelineBlock);
  const lastTimelineBlockWithFiles = useSelector(selectors.getLastTimelineBlockWithFiles);
  const needsSubmitterConfirmation = useSelector(selectors.needsSubmitterConfirmation);
  const canPerformSubmitterActions = useSelector(selectors.canPerformSubmitterActions);
  const canEditLastRevision = useSelector(selectors.canEditLastRevision);
  const {canComment} = useSelector(selectors.getDetails);
  const {fileTypes} = useSelector(selectors.getStaticData);
  const isLastBlock = lastTimelineBlock.id === block.id;
  const isLastValidBlock = lastValidTimelineBlock.id === block.id;
  const isLastTimelineBlockWithFiles = lastTimelineBlockWithFiles.id === block.id;
  const canEdit = isLastValidBlock && canEditLastRevision;
  const hasContent =
    block.commentHtml ||
    !!block.files.length ||
    !!block.tags.length ||
    !!block.customActions.length;
  const isAlwaysVisible = isLastValidBlock || isLastTimelineBlockWithFiles;
  const [visibilityToggle, setVisibilityToggle] = useState(false);
  const visible = visibilityToggle || isAlwaysVisible;
  const user = block.type.name === RevisionType.replacement ? INDICO_BOT_USER : block.user;

  return (
    <>
      <div className="i-timeline">
        <div className="i-timeline-item" styleName={isUndone ? 'undone-item' : undefined}>
          <UserAvatar user={user} />
          <div
            className={`i-timeline-item-box header-indicator-left ${
              !visible || !hasContent ? 'header-only' : ''
            }`}
            id={`block-info-${block.id}`}
          >
            <div className="i-box-header flexrow">
              <div className="f-self-stretch" styleName="item-header">
                {!!block.files.length && <span styleName="item-index">#{index}</span>}{' '}
                <span>
                  {block.header ? (
                    <strong>{block.header}</strong>
                  ) : (
                    <Translate>
                      <Param name="submitterName" value={user.fullName} wrapper={<strong />} /> has
                      submitted files
                    </Translate>
                  )}
                </span>{' '}
                <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}>
                  {serializeDate(createdDt, 'LLL')}
                </time>{' '}
                {modifiedDt && (
                  <time
                    dateTime={serializeDate(modifiedDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}
                    title={serializeDate(modifiedDt, 'LLL')}
                  >
                    <span className="review-comment-edited">
                      <Translate>edited</Translate>
                    </span>
                  </time>
                )}{' '}
                {isUndone && (
                  <Translate as="span" styleName="undone-indicator">
                    Retracted
                  </Translate>
                )}
              </div>
              {visible && canEdit && <ResetReview reviewURL={block.reviewURL} />}
              {!isAlwaysVisible && (hasContent || !!block.items.length) && (
                <a
                  className="i-link"
                  styleName="item-visibility-toggle"
                  onClick={() => setVisibilityToggle(!visible)}
                >
                  {visible ? <Translate>Hide</Translate> : <Translate>Show details</Translate>}
                </a>
              )}
              <StateIndicator state={RevisionTypeStates[block.type.name]} circular />
            </div>
            {visible && hasContent && (
              <div className="i-box-content">
                {isUndone && (
                  <Message warning>
                    <Icon name="warning sign" />
                    <Translate>This revision has been retracted by the editor.</Translate>
                  </Message>
                )}
                {block.commentHtml && <ReviewComment block={block} canEdit={canEdit} />}
                {block.commentHtml && !!(block.files.length || block.tags.length) && <Divider />}
                <FileDisplay
                  fileTypes={fileTypes}
                  files={block.files}
                  downloadURL={block.downloadFilesURL}
                  tags={block.tags}
                  outdated={!isLastTimelineBlockWithFiles}
                />
                {canPerformSubmitterActions && needsSubmitterConfirmation && isLastValidBlock && (
                  <ChangesConfirmation />
                )}
                {!!block.customActions.length && (
                  <CustomActions url={block.customActionURL} actions={block.customActions} />
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      {visible && (!!block.items.length || isLastBlock || isLastValidBlock) && (
        <RevisionLog items={block.items} separator={isLastBlock}>
          {isLastValidBlock && canComment && <ReviewForm />}
        </RevisionLog>
      )}
    </>
  );
}

TimelineItem.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
  index: PropTypes.number.isRequired,
};
