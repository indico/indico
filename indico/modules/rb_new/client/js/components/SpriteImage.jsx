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
import {connect} from 'react-redux';


class SpriteImage extends React.Component {
    static propTypes = {
        src: PropTypes.func.isRequired,
        pos: PropTypes.number.isRequired,
        roomsSpriteToken: PropTypes.string.isRequired,
        height: PropTypes.number,
        width: PropTypes.number,
        styles: PropTypes.object
    };

    static defaultProps = {
        width: 290,
        height: 170,
        styles: {}
    };

    render() {
        const {src, pos, width, height, roomsSpriteToken, styles} = this.props;
        const style = {
            background: `url(${src({version: roomsSpriteToken})}) -${pos * width}px 0`,
            height: `${height}px`,
            width: `${width}px`,
            ...styles
        };
        return <div style={style} className="img" />;
    }
}

const mapStateToProps = ({staticData: {roomsSpriteToken}}) => ({roomsSpriteToken});
export default connect(
    mapStateToProps
)(SpriteImage);
