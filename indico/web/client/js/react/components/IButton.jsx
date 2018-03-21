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

export default class IButton extends React.PureComponent {
    static propTypes = {
        classes: PropTypes.string,
        href: PropTypes.string,
        title: PropTypes.string,
        children: PropTypes.any,
        onClick: PropTypes.func,
    };

    static defaultProps = {
        classes: '',
        href: undefined,
        title: undefined,
        children: undefined,
        onClick: undefined,
    };

    render() {
        const {classes, href, title, children, onClick} = this.props;
        return (
            <a href={href} title={title} className={`i-button ${classes}`} onClick={onClick}>
                {children}
            </a>
        );
    }
}
