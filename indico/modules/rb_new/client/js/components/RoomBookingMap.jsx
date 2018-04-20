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
import ReactDOM from 'react-dom';
import Leaflet from 'leaflet';
import {Map, TileLayer, MapControl} from 'react-leaflet';
import {Checkbox} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import 'leaflet/dist/leaflet.css';
import './RoomBookingMap.module.scss';


export default function RoomBookingMap(props) {
    const {bounds, onMove, searchCheckbox, isSearchEnabled, onToggleSearchCheckbox} = props;
    return (
        <div styleName="map-container">
            <Map bounds={bounds} onDragend={onMove} onZoomend={onMove}>
                <TileLayer attribution='© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                           url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                {searchCheckbox && (
                    <RoomBookingMapControl position="topleft">
                        <Checkbox label={Translate.string('Search as I move the map')} onChange={onToggleSearchCheckbox}
                                  styleName="checkbox-control" checked={isSearchEnabled} />
                    </RoomBookingMapControl>
                )}
            </Map>
        </div>
    );
}

RoomBookingMap.propTypes = {
    bounds: propTypes.array.isRequired,
    onMove: propTypes.func.isRequired,
    searchCheckbox: propTypes.bool,
    isSearchEnabled: propTypes.bool,
    onToggleSearchCheckbox: propTypes.func,
};

RoomBookingMap.defaultProps = {
    searchCheckbox: false,
    isSearchEnabled: true,
    onToggleSearchCheckbox: null,
};


class RoomBookingMapControl extends MapControl {
    componentWillMount() {
        const {position, classes} = this.props;
        const mapControl = Leaflet.control({position});
        mapControl.onAdd = () => {
            const div = Leaflet.DomUtil.create('div', classes);
            Leaflet.DomEvent.disableClickPropagation(div);
            return div;
        };

        this.leafletElement = mapControl;
    }

    componentDidMount() {
        super.componentDidMount();
        this.renderControl();
    }

    componentDidUpdate(next) {
        super.componentDidUpdate(next);
        this.renderControl();
    }

    componentWillUnmount() {
        ReactDOM.unmountComponentAtNode(this.leafletElement.getContainer());
    }

    renderControl() {
        const container = this.leafletElement.getContainer();
        ReactDOM.render(React.Children.only(this.props.children), container);
    }
}

RoomBookingMapControl.propTypes = {
    position: propTypes.string.isRequired,
    classes: propTypes.string,
};

RoomBookingMapControl.defaultProps = {
    classes: '',
};
