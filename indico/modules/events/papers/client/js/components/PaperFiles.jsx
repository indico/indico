// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

export default function PaperFiles({fullWidth, files}) {
  return (
    <ul className={`paper-files flexrow f-wrap f-a-center ${fullWidth ? 'full-width' : ''}`}>
      {files.map(file => (
        <li key={file.id}>
          <a
            href={file.downloadURL}
            className={`attachment paper-file i-button text-color borderless ${file.icon}`}
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
