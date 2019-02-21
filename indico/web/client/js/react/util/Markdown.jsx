/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import React from 'react';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';

// eslint-disable-next-line react/prop-types
const ExternalLink = ({href, children}) => (
    <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
);


/**
 * This component wraps ReactMarkdown and provides some convenience props.
 */
const Markdown = ({targetBlank, ...props}) => {
    if (targetBlank) {
        // XXX: not using linkTarget since that doesn't set noopener
        props.renderers = {link: ExternalLink, linkReference: ExternalLink, ...props.renderers};
    }
    return <ReactMarkdown {...props} />;
};

Markdown.propTypes = {
    source: PropTypes.string.isRequired,
    renderers: PropTypes.object,
    targetBlank: PropTypes.bool,
    // see https://github.com/rexxars/react-markdown#options for more props
};

Markdown.defaultProps = {
    targetBlank: false,
    renderers: {},
};


export default Markdown;
