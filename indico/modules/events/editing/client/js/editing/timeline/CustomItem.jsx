// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {FinalRevisionState} from '../../models';

import ResetReview from './ResetReview';
import * as selectors from './selectors';
import StateIndicator from './StateIndicator';
import {blockItemPropTypes} from './util';

import '../../../styles/timeline.module.scss';

export default function CustomItem({
  item: {header, user, reviewedDt, html, revisionId, undoneJudgement},
  state,
}) {
  const lastRevertableRevisionId = useSelector(selectors.getLastRevertableRevisionId);
  const isUndone = undoneJudgement && undoneJudgement.name !== FinalRevisionState.none;
  state = isUndone ? undoneJudgement.name : state;

  return (
    <div className="i-timeline-item" styleName={isUndone ? 'undone-item' : undefined}>
      <UserAvatar user={user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box">
          <div
            className={`i-box-header flexrow ${!html ? 'header-only' : ''}`}
            style={{alignItems: 'center'}}
          >
            <div className="f-self-stretch" styleName="item-header">
              {header}{' '}
              <time dateTime={serializeDate(reviewedDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}>
                {serializeDate(reviewedDt, 'LL')}
              </time>{' '}
              {isUndone && (
                <Translate as="span" styleName="undone-indicator">
                  Retracted
                </Translate>
              )}
            </div>
            {!isUndone && revisionId === lastRevertableRevisionId && (
              <ResetReview revisionId={revisionId} />
            )}
            {state && <StateIndicator state={state} circular basic={isUndone} />}
          </div>
          {html && (
            <div className="i-box-content js-form-container">
              <div className="markdown-text" dangerouslySetInnerHTML={{__html: html}} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

CustomItem.propTypes = {
  item: PropTypes.shape(blockItemPropTypes).isRequired,
  state: PropTypes.string,
};

CustomItem.defaultProps = {
  state: null,
};
