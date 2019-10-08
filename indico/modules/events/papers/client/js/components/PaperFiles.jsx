// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import paperFileDownloadURL from 'indico-url:papers.download_file';

import React from 'react';
import {useSelector} from 'react-redux';
import PropTypes from 'prop-types';
import {getPaperDetails} from '../selectors';

export default function PaperFiles({fullWidth, files}) {
  const {
    event: {id: eventId},
    contribution: {id: contributionId},
  } = useSelector(getPaperDetails);

  return (
    <ul className={`paper-files flexrow f-wrap f-a-center ${fullWidth ? 'full-width' : ''}`}>
      {files.map(file => (
        <li key={file.id}>
          <a
            href={paperFileDownloadURL({
              file_id: file.id,
              filename: file.filename,
              confId: eventId,
              contrib_id: contributionId,
            })}
            className={`attachment paper-file i-button text-color borderless ${file.icon}`}
            title={file.filename}
          >
            <span className="title truncate-text">{file.filename}</span>
          </a>
        </li>
      ))}
    </ul>
  );
}

PaperFiles.propTypes = {
  files: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      filename: PropTypes.string.isRequired,
      icon: PropTypes.string.isRequired,
    })
  ).isRequired,
  fullWidth: PropTypes.bool,
};

PaperFiles.defaultProps = {
  fullWidth: false,
};
