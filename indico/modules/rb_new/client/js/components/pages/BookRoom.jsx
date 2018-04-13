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

import propTypes from 'prop-types';
import React from 'react';
import filterBarFactory from '../../containers/FilterBar';
import {Row, Col} from 'antd';
import {Translate} from 'indico/react/i18n';

import RoomBookingMap from "../RoomBookingMap";

export default class BookRoom extends React.Component {
    static propTypes = {
        fetchMapDefaultLocation: propTypes.func.isRequired,
        mapLocation: propTypes.object
    };

    static defaultProps = {
        mapLocation: null
    };

    constructor(props) {
        super(props);
        const {fetchMapDefaultLocation, mapLocation} = props;
        if (!mapLocation) {
            fetchMapDefaultLocation();
        }
    }

    render() {
        const {mapLocation} = this.props;
        const FilterBar = filterBarFactory('bookRoom');
        return (
            <Row>
                <Col span={16}>
                    <FilterBar />
                </Col>
                <Col span={8}>
                    {mapLocation && <RoomBookingMap center={mapLocation.center} zoom={mapLocation.zoom} />}
                </Col>
            </Row>
        );
    }
}
