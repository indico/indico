// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionDisplayURL from 'indico-url:contributions.display_contribution';

import React from 'react';
import {useSelector} from 'react-redux';

import {Param, Translate} from 'indico/react/i18n';
import {MathJax} from 'indico/react/components';

import {getPaperDetails} from '../selectors';
import PaperContent from './PaperContent';

export default function PaperInfo() {
  const {
    contribution,
    state,
    lastRevision: {submitter},
    event: {id: eventId},
  } = useSelector(getPaperDetails);

  return (
    <>
      <div className="submission-title flexrow">
        <MathJax>
          <h3 className="f-self-strech">
            <Translate>
              Paper for <Param name="title" value={contribution.title} />
            </Translate>{' '}
            <span className="submission-id">#{contribution.friendlyId}</span>
          </h3>
        </MathJax>
      </div>
      <div className="paper-public">
        <div className="review-summary flexrow f-a-baseline">
          <div className="review-summary-badge">
            <div className={`i-tag ${state.cssClass}`}>{state.title}</div>
          </div>
          <div className="review-summary-content f-self-stretch">
            <div>
              <Translate>
                <Param name="submitterName" value={submitter.fullName} wrapper={<strong />} />{' '}
                submitted this paper for the contribution{' '}
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
        <div className="review-item-content">
          <PaperContent />
        </div>
      </div>
    </>
  );
}
