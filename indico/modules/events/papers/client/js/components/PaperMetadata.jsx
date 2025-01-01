// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import {useSelector} from 'react-redux';

import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {getPaperDetails} from '../selectors';

export default function PaperMetadata() {
  const {
    lastRevision: {id, submittedDt, submitter},
  } = useSelector(getPaperDetails);

  const date = (
    <a className="paper-metadata-dt" href={`#block-info-${id}`}>
      <time dateTime={serializeDate(submittedDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}>
        {serializeDate(submittedDt, 'LL')}
      </time>
    </a>
  );

  return (
    <div className="paper-metadata flexrow f-j-end">
      <Translate>
        Submitted on <Param name="date" value={date} /> by{' '}
        <Param name="submitter" value={submitter.fullName} />
      </Translate>
    </div>
  );
}
