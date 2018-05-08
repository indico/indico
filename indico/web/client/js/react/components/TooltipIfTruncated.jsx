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


export default class TooltipIfTruncated extends React.Component {
    static propTypes = {
        children: PropTypes.any.isRequired
    };

    mouseEnter(event) {
        const element = event.target;
        const overflows = element.offsetWidth < element.scrollWidth || element.offsetHeight < element.scrollHeight;

        if (overflows && !element.getAttribute('title')) {
            element.setAttribute('title', element.innerText);
        }
    }

    render() {
        const {children} = this.props;
        const child = React.Children.only(children);
        return React.cloneElement(child, {onMouseEnter: (event) => this.mouseEnter(event)});
    }
}
