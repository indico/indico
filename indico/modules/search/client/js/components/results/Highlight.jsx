// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

export default function Highlight({text, highlight}) {
  if (highlight?.length) {
    return highlight
      .slice(0, 3) // eslint-disable-next-line react/no-array-index-key
      .map((html, idx) => <div key={html + idx} dangerouslySetInnerHTML={{__html: html}} />);
  }
  return <span>{text.slice(0, 240)}</span>;
}

Highlight.propTypes = {
  text: PropTypes.string.isRequired,
  highlight: PropTypes.arrayOf(PropTypes.string),
};

Highlight.defaultProps = {
  highlight: [],
};
