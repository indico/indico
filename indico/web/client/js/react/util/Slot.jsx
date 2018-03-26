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


export default class Slot extends React.Component {
    static propTypes = {
        // eslint-disable-next-line react/no-unused-prop-types
        name: PropTypes.string
    };

    static defaultProps = {
        name: 'content'
    };

    static split(children) {
        if (children.every((e) => (React.isValidElement(e) && e.type === Slot))) {
            const result = {};
            React.Children.forEach(children, (child) => {
                result[child.props.name] = child.props.children;
            });
            return result;
        } else {
            return {
                content: children
            };
        }
    }
}
