/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import './DimmableImage.module.scss';


export default class DimmableImage extends React.Component {
    static propTypes = {
        children: PropTypes.node.isRequired,
        content: PropTypes.node,
        hoverContent: PropTypes.node,
    };

    static defaultProps = {
        content: null,
        hoverContent: null,
    };

    render() {
        const {children, content, hoverContent} = this.props;

        return (
            <div styleName="dimmable-image">
                {children}
                <div styleName="content">
                    {content}
                </div>
                <div styleName="hover-content">
                    {hoverContent}
                </div>
            </div>
        );
    }
}
