// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import '../ResultList.module.scss';

export default function Highlight({text, highlight}) {
  if (highlight?.length) {
    return (
      <div styleName="summary">
        {highlight.slice(0, 3).map((html, idx) => (
          // eslint-disable-next-line react/no-array-index-key
          <div key={html + idx} dangerouslySetInnerHTML={{__html: html}} />
        ))}
      </div>
    );
  }
  return text ? <div styleName="summary">{text.slice(0, 240)}</div> : null;
}

Highlight.propTypes = {
  text: PropTypes.string.isRequired,
  highlight: PropTypes.arrayOf(PropTypes.string),
};

Highlight.defaultProps = {
  highlight: [],
};
