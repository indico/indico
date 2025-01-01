// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Leaflet from 'leaflet';
import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import {MapControl, withLeaflet} from 'react-leaflet';

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
