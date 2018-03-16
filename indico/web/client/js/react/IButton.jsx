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

export default class IButton extends React.Component {
    render() {
        const {id, classes, href, title, name, children} = this.props;
        return (
            <a id={id} className={`i-button ${classes || ''}`}
                href={href} title={title}>
                {name}{children}
            </a>
        );
    }
}

IButton.propTypes = {
    id: PropTypes.string,
    classes: PropTypes.string,
    href: PropTypes.string,
    title: PropTypes.string,
    name: PropTypes.string,
    children: PropTypes.node
};
