// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import paperFileDownloadURL from 'indico-url:papers.download_file';

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {useSelector} from 'react-redux';
import moment from 'moment';

import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import UserAvatar from './UserAvatar';
import {getPaperEvent, getPaperContribution} from '../selectors';

export default function RevisionInfo({revision}) {
  const {submitter, isLastRevision, id, number, submittedDt, files} = revision;
  const submitterName = submitter.isSystem ? Translate.string('A User') : submitter.fullName;
  const contribution = useSelector(getPaperContribution);
  const event = useSelector(getPaperEvent);

  return (
    <div className="i-timeline">
      <div className="i-timeline-item">
        <UserAvatar user={submitter} />
        <div
          className={`i-timeline-item-box header-indicator-left ${
            !isLastRevision ? 'header-only' : ''
          }`}
          id={`revision-info-${id}`}
        >
          <div className="i-box-header flexrow">
            <div className="f-self-stretch">
              <Translate>
                <Param name="submitterName" value={submitterName} wrapper={<strong />} /> submitted
                paper revision #
                <Param name="revisionNumber" value={number} />{' '}
              </Translate>
              <time dateTime={serializeDate(submittedDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(submittedDt, 'D MMM YYYY')}
              </time>
            </div>
            {!isLastRevision && (
              <a
                href="#"
                className="revision-info-link i-link"
                data-toggle={`#revision-timeline-${id}, #revision-info-${id} .submission-info`}
                data-toggle-class={`{"target": "#revision-info-${id}", "class": "header-only"}`}
                data-show-text={Translate.string('Show old revision')}
                data-hide-text={Translate.string('Hide old revision')}
              >
                <Translate>Show old revision</Translate>
              </a>
            )}
          </div>
          <div className={`i-box-content submission-info ${!isLastRevision ? 'weak-hidden' : ''}`}>
            <ul className="file-list">
              {_.sortBy(files, 'filename').map(file => (
                <li className="truncate-text" key={file.id}>
                  <a
                    href={paperFileDownloadURL({
                      file_id: file.id,
                      filename: file.filename,
                      confId: event.id,
                      contrib_id: contribution.id,
                    })}
                    className={`attachment ${file.icon}`}
                    title={file.filename}
                  >
                    {' '}
                    <span className="title">{file.filename}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

RevisionInfo.propTypes = {
  revision: PropTypes.object.isRequired,
};
