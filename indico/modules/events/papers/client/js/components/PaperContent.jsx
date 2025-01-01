// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useSelector} from 'react-redux';

import {Translate} from 'indico/react/i18n';

import {getPaperDetails} from '../selectors';

import PaperFiles from './PaperFiles';
import PaperMetadata from './PaperMetadata';

export default function PaperContent() {
  const {
    lastRevision: {spotlightFile, files},
  } = useSelector(getPaperDetails);
  const onlySpotlightFile = files.length === 1;
  let content;

  if (spotlightFile) {
    content = (
      <>
        <div
          key={`spotlight-file-${spotlightFile.id}`}
          className={`flexrow f-a-center spotlight-file i-button text-color borderless paper-file ${
            onlySpotlightFile ? 'full-width' : ''
          }`}
        >
          <a
            href={spotlightFile.downloadURL}
            className={`attachment spotlight-file-name flexrow f-a-center truncate-text ${spotlightFile.icon}`}
          >
            <span className="title truncate-text">{spotlightFile.filename}</span>
          </a>
        </div>
        {!onlySpotlightFile && (
          <PaperFiles
            key="paper-files"
            files={files.filter(file => file.id !== spotlightFile.id)}
          />
        )}
      </>
    );
  } else {
    content = (
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
