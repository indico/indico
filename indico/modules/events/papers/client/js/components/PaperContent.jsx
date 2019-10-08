// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import paperFileDownloadURL from 'indico-url:papers.download_file';

import React from 'react';
import {useSelector} from 'react-redux';

import {Translate} from 'indico/react/i18n';

import {getPaperDetails} from '../selectors';
import PaperFiles from './PaperFiles';
import PaperMetadata from './PaperMetadata';

export default function PaperContent() {
  const {
    lastRevision: {spotlightFile, files},
    event: {id: eventId},
    contribution: {id: contributionId},
  } = useSelector(getPaperDetails);
  const onlySpotlightFile = files.length === 1;
  const content = [];

  if (spotlightFile) {
    content.push(
      <div
        key={`spotlight-file-${spotlightFile.id}`}
        className={`flexrow f-a-center spotlight-file i-button text-color borderless paper-file ${
          onlySpotlightFile ? 'full-width' : ''
        }`}
        title={spotlightFile.filename}
      >
        <a
          href={paperFileDownloadURL({
            file_id: spotlightFile.id,
            filename: spotlightFile.filename,
            confId: eventId,
            contrib_id: contributionId,
          })}
          className={`attachment spotlight-file-name flexrow f-a-center truncate-text ${spotlightFile.icon}`}
        >
          <span className="title truncate-text">{spotlightFile.filename}</span>
        </a>
      </div>
    );

    if (!onlySpotlightFile) {
      content.push(
        <PaperFiles key="paper-files" files={files.filter(file => file.id !== spotlightFile.id)} />
      );
    }
  } else {
    content.push(
      <div key="paper-files" className="paper-files-list flexrow f-a-baseline">
        <div className="paper-files-list-label f-self-no-shrink">
          <Translate>Paper files</Translate>
        </div>
        <PaperFiles files={files} fullWidth />
      </div>
    );
  }

  return (
    <div className="paper-content flexcol">
      <div className="flexrow">{content}</div>
      <PaperMetadata />
    </div>
  );
}
