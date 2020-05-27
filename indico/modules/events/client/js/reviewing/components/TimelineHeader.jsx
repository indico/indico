// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionDisplayURL from 'indico-url:contributions.display_contribution';

import React from 'react';
import PropTypes from 'prop-types';

import {Message, Icon} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {MathJax} from 'indico/react/components';

export default function TimelineHeader({
  children,
  contribution,
  state,
  submitter,
  eventId,
  reviewConditionsValid,
  canEdit,
  editingEnabled,
}) {
  return (
    <>
      <div className="submission-title flexrow">
        <MathJax>
          <h3 className="f-self-strech">
            {contribution.title} <span className="submission-id">#{contribution.friendlyId}</span>
            {contribution.code && <span className="submission-code">{contribution.code}</span>}
          </h3>
        </MathJax>
      </div>
      <div className="paper-public">
        <div className="review-summary flexrow f-a-baseline">
          <div className="review-summary-badge">
            {reviewConditionsValid ? (
              <div className={`i-tag ${state.cssClass}`}>{state.title}</div>
            ) : (
              <div className="i-tag">
                <Translate>Not Ready</Translate>
              </div>
            )}
          </div>
          <div className="review-summary-content f-self-stretch">
            <div>
              <Translate>
                <Param name="submitterName" value={submitter.fullName} wrapper={<strong />} />{' '}
                submitted for the contribution{' '}
                <Param
                  name="contributionLink"
                  value={contribution.title}
                  wrapper={
                    <a
                      href={contributionDisplayURL({contrib_id: contribution.id, confId: eventId})}
                    />
                  }
                />
              </Translate>{' '}
            </div>
          </div>
        </div>
        {!reviewConditionsValid && (
          <Message warning>
            <Icon name="warning sign" />
            <Translate>This editable is not fulfilling reviewing conditions.</Translate>
          </Message>
        )}
        {!editingEnabled && (
          <Message warning>
            <Icon name="warning sign" />
            <Translate>Editing is currently not enabled.</Translate>
            {canEdit && (
              <>
                {' '}
                <Translate>Since you are a manager you can edit anyway.</Translate>
              </>
            )}
          </Message>
        )}
        <div className="review-item-content">{children}</div>
      </div>
    </>
  );
}

TimelineHeader.propTypes = {
  contribution: PropTypes.shape({
    id: PropTypes.number.isRequired,
    friendlyId: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    code: PropTypes.string.isRequired,
  }).isRequired,
  state: PropTypes.shape({
    cssClass: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
  }).isRequired,
  submitter: PropTypes.shape({
    fullName: PropTypes.string.isRequired,
  }).isRequired,
  eventId: PropTypes.number.isRequired,
  children: PropTypes.node.isRequired,
  reviewConditionsValid: PropTypes.bool,
  canEdit: PropTypes.bool,
  editingEnabled: PropTypes.bool,
};

TimelineHeader.defaultProps = {
  reviewConditionsValid: true,
  canEdit: true,
  editingEnabled: true,
};
