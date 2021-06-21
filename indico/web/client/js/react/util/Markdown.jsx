// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import ReactMarkdown from 'react-markdown';

// eslint-disable-next-line react/prop-types
const ExternalLink = ({href, children}) => (
  <a href={href} target="_blank" rel="noopener noreferrer">
    {children}
  </a>
);

/**
 * This component wraps ReactMarkdown and provides some convenience props.
 */
const Markdown = ({targetBlank, ...props}) => {
  if (targetBlank) {
    // XXX: not using linkTarget since that doesn't set noopener
    props.components = {a: ExternalLink, ...props.components};
  }
  return <ReactMarkdown {...props} />;
};

Markdown.propTypes = {
  children: PropTypes.string.isRequired,
  components: PropTypes.object,
  targetBlank: PropTypes.bool,
  // see https://github.com/rexxars/react-markdown#options for more props
};

Markdown.defaultProps = {
  targetBlank: false,
  components: {},
};

export default Markdown;
