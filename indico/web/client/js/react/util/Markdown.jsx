// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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
const Markdown = ({targetBlank, remarkPlugins, ...props}) => {
  if (targetBlank) {
    // XXX: not using linkTarget since that doesn't set noopener
    props.components = {a: ExternalLink, ...props.components};
  }
  return <ReactMarkdown {...props} remarkPlugins={remarkPlugins} />;
};

Markdown.propTypes = {
  children: PropTypes.string.isRequired,
  components: PropTypes.object,
  targetBlank: PropTypes.bool,
  remarkPlugins: ReactMarkdown.propTypes.remarkPlugins,
  // see https://github.com/rexxars/react-markdown#options for more props
};

Markdown.defaultProps = {
  targetBlank: false,
  components: {},
  remarkPlugins: [],
};

export default Markdown;
