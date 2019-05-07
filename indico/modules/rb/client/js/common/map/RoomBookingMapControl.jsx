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

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import {MapControl, withLeaflet} from 'react-leaflet';
import Leaflet from 'leaflet';


class RoomBookingMapControl extends MapControl {
    static propTypes = {
        position: PropTypes.string.isRequired,
        classes: PropTypes.string,
    };

    static defaultProps = {
        classes: '',
    };

    componentDidMount() {
        super.componentDidMount();
        this.renderControl();
    }

    componentDidUpdate(prevProps) {
        const {classes} = this.props;
        super.componentDidUpdate(prevProps);
        this.renderControl();
        if (classes) {
            this.leafletElement.getContainer().classList.add(...classes.trim().split(' '));
        }
    }

    componentWillUnmount() {
        ReactDOM.unmountComponentAtNode(this.leafletElement.getContainer());
    }

    createLeafletElement(props) {
        const {position, classes} = props;
        const mapControl = Leaflet.control({position});
        mapControl.onAdd = () => {
            const div = Leaflet.DomUtil.create('div', classes);
            Leaflet.DomEvent.disableClickPropagation(div);
            Leaflet.DomEvent.disableScrollPropagation(div);
            return div;
        };
        return mapControl;
    }

    renderControl() {
        const container = this.leafletElement.getContainer();
        ReactDOM.render(React.Children.only(this.props.children), container);
    }
}

export default withLeaflet(RoomBookingMapControl);
