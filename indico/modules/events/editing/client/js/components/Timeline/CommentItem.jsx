// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import PropTypes from 'prop-types';
import {Button, Confirm} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {deleteRevisionComment} from '../../actions';
import {getLastRevision} from '../../selectors';

const INDICO_BOT_USER = {
  fullName: 'Indico Bot',
  avatarBgColor: '#8f8f8f',
};

export default function Comment({
  revisionId,
  user,
  createdDt,
  modifiedDt,
  html,
  internal,
  system,
  canModify,
  modifyCommentURL,
}) {
  const [isDeletingComment, setIsDeletingComment] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const lastRevision = useSelector(getLastRevision);
  const dispatch = useDispatch();
  const commentUser = system ? INDICO_BOT_USER : user;

  return (
    <div className="i-timeline-item">
      <UserAvatar user={commentUser} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box header-indicator-left">
          <div className="i-box-header flexrow">
            <div className="f-self-stretch">
              <Translate>
                <Param name="userName" value={commentUser.fullName} wrapper={<strong />} /> left a
                comment
              </Translate>{' '}
              {internal && (
                <i
                  className="review-comment-visibility internal icon-shield"
                  title={Translate.string('Visible only to editors')}
                />
              )}
              <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(createdDt, 'LL')}
              </time>
              {modifiedDt && (
                <span
                  className="review-comment-edited"
                  title={Translate.string('On {modificationDate}', {
                    modificationDate: serializeDate(modifiedDt, 'LL'),
                  })}
                >
                  {' '}
                  · <Translate>edited</Translate>
                </span>
              )}
            </div>
            {canModify && lastRevision.id === revisionId && (
              <>
                <a
                  onClick={() => setConfirmOpen(true)}
                  className="i-link icon-cross js-delete-comment"
                  title={Translate.string('Remove comment')}
                />
                <Confirm
                  size="tiny"
                  header={Translate.string('Remove comment')}
                  open={confirmOpen}
                  content={Translate.string('Are you sure you want to remove this comment?')}
                  closeOnDimmerClick={!isDeletingComment}
                  closeOnEscape={!isDeletingComment}
                  onCancel={() => setConfirmOpen(false)}
                  onConfirm={async () => {
                    setIsDeletingComment(true);

                    const rv = await dispatch(deleteRevisionComment(modifyCommentURL));
                    if (!rv.error) {
                      setConfirmOpen(false);
                    }

                    setIsDeletingComment(false);
                  }}
                  cancelButton={
                    <Button content={Translate.string('Cancel')} disabled={isDeletingComment} />
                  }
                  confirmButton={
                    <Button
                      content={Translate.string('Remove comment')}
                      loading={isDeletingComment}
                      disabled={isDeletingComment}
                      negative
                    />
                  }
                  closeIcon={!isDeletingComment}
                />
              </>
            )}
          </div>
          <div className="i-box-content js-form-container">
            <div className="markdown-text" dangerouslySetInnerHTML={{__html: html}} />
          </div>
        </div>
      </div>
    </div>
  );
}

Comment.propTypes = {
  revisionId: PropTypes.number.isRequired,
  createdDt: PropTypes.string.isRequired,
  html: PropTypes.string.isRequired,
  canModify: PropTypes.bool.isRequired,
  modifyCommentURL: PropTypes.string.isRequired,
  user: PropTypes.shape({
    fullName: PropTypes.string.isRequired,
    avatarBgColor: PropTypes.string.isRequired,
  }),
  modifiedDt: PropTypes.string,
  internal: PropTypes.bool,
  system: PropTypes.bool,
};

Comment.defaultProps = {
  user: null,
  modifiedDt: null,
  internal: false,
  system: false,
};
