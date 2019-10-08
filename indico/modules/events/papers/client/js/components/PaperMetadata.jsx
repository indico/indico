// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import moment from 'moment';
import {useSelector} from 'react-redux';

import {serializeDate} from 'indico/utils/date';
import {getPaperDetails} from '../selectors';

export default function PaperMetadata() {
  const {
    lastRevision: {id, submittedDt, submitter},
  } = useSelector(getPaperDetails);

  return (
    <div className="paper-metadata flexrow f-j-end">
      Submitted on{' '}
      <a className="paper-metadata-dt" href={`#revision-info-${id}`}>
        <time dateTime={serializeDate(submittedDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
          {serializeDate(submittedDt, 'D MMM YYYY')}
        </time>
      </a>{' '}
      by {submitter.fullName}
    </div>
  );
}
