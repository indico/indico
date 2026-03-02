// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import {List, Loader} from 'semantic-ui-react';

import {TooltipIfTruncated} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import './ContributionList.module.scss';
import {Contribution, ContributionRecord} from './types';

interface ContributionList {
  loading?: boolean;
  contributions: ContributionRecord | null;
  title?: string;
  emptyText?: string;
  actionsElement?: (contribution: Contribution) => React.ReactNode;
  hideWhenEmpty?: boolean;
}

export function ContributionList({
  loading,
  contributions,
  title,
  actionsElement,
  emptyText,
  hideWhenEmpty = true,
}: ContributionList) {
  if (hideWhenEmpty && contributions === null) {
    return null;
  }

  return (
    <section>
      {title && (
        <div className="header">
          <div className="header-row">
            <h3>{title}</h3>
          </div>
        </div>
      )}
      <div styleName="contribution-container">
        <div className="i-box just-group-list">
          <div className="i-box-content">
            {loading ? (
              <Loader active inline styleName="contrib-loader" />
            ) : contributions !== null && Object.keys(contributions).length > 0 ? (
              <List celled styleName="contrib-list">
                {Object.values(contributions).map(contribution => (
                  <List.Item key={contribution.id} styleName="contrib-item">
                    <List.Content>
                      <div styleName="list-flex">
                        <span styleName="date-span">
                          {contribution.start_dt ? (
                            <>
                              <span>{moment(contribution.start_dt).format('D MMM YYYY')}</span>
                              <br />
                              <span styleName="date-span-time">
                                {moment(contribution.start_dt).format('HH:MM')}
                              </span>
                            </>
                          ) : (
                            <Translate>Not Scheduled</Translate>
                          )}
                        </span>
                        <span styleName="contribution-name-box">
                          <a href={contribution.url} target="_blank" rel="noopener noreferrer">
                            {contribution.title}
                          </a>
                          <br />
                          <TooltipIfTruncated>
                            <span styleName="detail">{contribution.description ?? ''}</span>
                          </TooltipIfTruncated>
                        </span>
                        {actionsElement && actionsElement(contribution)}
                      </div>
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            ) : (
              <div styleName="empty">{emptyText ?? ''}</div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
