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


export default class SpriteImage extends React.Component {
    static propTypes = {
        src: PropTypes.string.isRequired,
        pos: PropTypes.number.isRequired,
        height: PropTypes.number,
        width: PropTypes.number,
        styles: PropTypes.object,
        scale: PropTypes.string,
        origin: PropTypes.string
    };

    static defaultProps = {
        width: 290,
        height: 170,
        styles: {},
        scale: null,
        origin: null
    };

    render() {
        const {src, pos, width, height, styles, scale, origin} = this.props;
        const style = {
            background: `url(${src}) -${pos * width}px 0`,
            height: `${height}px`,
            width: `${width}px`,
            ...styles
        };

        if (origin && scale) {
            style.transformOrigin = origin;
            style.transform = `scale(${scale})`;
        }

        return <div style={style} className="img" />;
    }
}
