// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {Button, Checkbox, Dimmer, Dropdown, Loader, Popup, Sticky} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {actions as filtersActions} from '../filters';

import * as mapActions from './actions';
import RoomBookingMap from './RoomBookingMap';
import RoomBookingMapControl from './RoomBookingMapControl';
import * as mapSelectors from './selectors';
import {getAreaBounds, getMapBounds, getRoomListBounds, checkRoomsInBounds} from './util';

import './MapController.module.scss';

class MapController extends React.Component {
  static propTypes = {
    areas: PropTypes.array.isRequired,
    rooms: PropTypes.arrayOf(PropTypes.object).isRequired,
    searchEnabled: PropTypes.bool.isRequired,
    onRoomClick: PropTypes.func.isRequired,
    mapData: PropTypes.shape({
      bounds: PropTypes.object,
      filterBounds: PropTypes.object,
    }).isRequired,
    actions: PropTypes.exact({
      toggleMapSearch: PropTypes.func.isRequired,
      updateLocation: PropTypes.func.isRequired,
      // XXX: this seemingly unused action may be used by plugins!
      // eslint-disable-next-line react/no-unused-prop-types
      setFilterParameter: PropTypes.func.isRequired,
    }).isRequired,
  };

  constructor(props) {
    super(props);
    this.mapRef = React.createRef();
    this.contextRef = React.createRef();
  }

  state = {
    loading: true,
    allRoomsVisible: false,
    searchVisible: false,
  };

  static getDerivedStateFromProps(props, prevState) {
    const {
      mapData: {bounds, filterBounds},
    } = props;
    const areaBounds = filterBounds || bounds;
    const prevProps = prevState.prevProps || props;
    if (!_.isEqual(prevProps, props)) {
      return {
        ...prevState,
        areaBounds,
        prevProps: props,
      };
    } else {
      return {
        areaBounds,
        ...prevState,
        prevProps,
      };
    }
  }

  componentDidUpdate(prevProps) {
    const {
      mapData: {bounds},
      rooms,
    } = this.props;
    const {
      mapData: {bounds: prevBounds},
      rooms: prevRooms,
    } = prevProps;
    if (bounds === prevBounds && rooms === prevRooms) {
      return;
    }

    // check whether rooms are in bounds in parallel, to
    // avoid blocking the main thread with the calculations
    _.defer(() => {
      const {allRoomsVisible} = this.state;
      const inBounds = !bounds || checkRoomsInBounds(rooms, bounds);
      if (inBounds !== allRoomsVisible) {
        this.setState({
          allRoomsVisible: !rooms.length || inBounds,
        });
      }
    });
  }

  onMapLoad = async () => {
    const {
      mapData: {filterBounds},
      actions: {toggleMapSearch},
    } = this.props;
    this.updateToMapBounds();
    toggleMapSearch(!_.isEmpty(filterBounds), filterBounds);
    this.setState({
      loading: false,
    });
  };

  onMove = e => {
    const {
      searchEnabled,
      actions: {updateLocation},
    } = this.props;
    updateLocation(getMapBounds(e.target), searchEnabled);
  };

  onTouch = () => {
    this.setState({searchVisible: true});
  };

  onChangeArea(areaIndex) {
    const {areas} = this.props;
    this.setState({
      areaBounds: getAreaBounds(areas[areaIndex]),
    });
  }

  updateToMapBounds = () => {
    const {
      searchEnabled,
      actions: {updateLocation},
    } = this.props;
    if (this.mapRef.current) {
      const map = this.mapRef.current.leafletElement;
      updateLocation(getMapBounds(map), searchEnabled);
    }
  };

  showAllRooms = () => {
    const {rooms} = this.props;
    this.setState({
      areaBounds: getRoomListBounds(rooms),
      allRoomsVisible: true,
    });
  };

  render() {
    const {
      searchEnabled,
      rooms,
      areas,
      actions,
      onRoomClick,
      mapData: {bounds},
      actions: {toggleMapSearch},
    } = this.props;
    const {areaBounds, loading, allRoomsVisible, searchVisible} = this.state;
    const areaOptions = Object.entries(areas).map(([key, val]) => ({
      text: val.name,
      value: Number(key),
    }));

    const searchControl = (
      <RoomBookingMapControl
        position="topleft"
        classes={`search-control ${searchVisible || searchEnabled ? 'visible' : ''}`}
      >
        <Checkbox
          label={Translate.string('Show only rooms in this area')}
          checked={searchEnabled}
          onChange={(e, data) => toggleMapSearch(data.checked, bounds)}
          styleName="map-control-content"
        />
      </RoomBookingMapControl>
    );

    const areasControl = !!areas.length && (
      <RoomBookingMapControl position="bottomleft">
        <Dropdown
          placeholder={Translate.string('Select area')}
          selection
          upward
          options={areaOptions}
          value={null}
          styleName="areas-dropdown map-control-content"
          openOnFocus={false}
          onChange={(e, data) => this.onChangeArea(data.value)}
        />
      </RoomBookingMapControl>
    );

    const showAllButton = (
      <Button
        icon="expand"
        styleName="show-all-button map-control-content"
        onClick={this.showAllRooms}
        disabled={allRoomsVisible}
      />
    );

    const showAllControl = (
      <RoomBookingMapControl position="bottomright">
        <Popup
          trigger={showAllButton}
          content={Translate.string('Zoom out to include all listed rooms')}
        />
      </RoomBookingMapControl>
    );

    return (
      <div styleName="map-context" ref={this.contextRef}>
        <Sticky context={this.contextRef.current} offset={30}>
          <Dimmer.Dimmable>
            <Dimmer inverted active={loading} styleName="map-dimmer">
              <Loader />
            </Dimmer>
            {!!areaBounds && (
              <RoomBookingMap
                mapRef={this.mapRef}
                bounds={areaBounds}
                rooms={rooms}
                onLoad={this.onMapLoad}
                onMove={this.onMove}
                onTouch={this.onTouch}
                onRoomClick={onRoomClick}
                actions={actions}
              >
                <>
                  {searchControl}
                  {areasControl}
                  {showAllControl}
                </>
              </RoomBookingMap>
            )}
          </Dimmer.Dimmable>
        </Sticky>
      </div>
    );
  }
}

export default function mapControllerFactory(namespace, searchRoomSelectors) {
  const getMapData = mapSelectors.makeGetMapData(namespace);
  const isMapSearchEnabled = mapSelectors.makeIsMapSearchEnabled(namespace);
  return connect(
    state => ({
      areas: mapSelectors.getMapAreas(state),
      rooms: searchRoomSelectors.getSearchResultsForMap(state),
      mapData: getMapData(state),
      searchEnabled: isMapSearchEnabled(state),
    }),
    dispatch => ({
      actions: {
        updateLocation: (location, search) => {
          dispatch(mapActions.updateLocation(namespace, location));
          if (search) {
            dispatch(filtersActions.setFilterParameter(namespace, 'bounds', location));
          }
        },
        toggleMapSearch: (search, location) => {
          dispatch(mapActions.toggleMapSearch(namespace, search));
          dispatch(
            filtersActions.setFilterParameter(namespace, 'bounds', search ? location : null)
          );
        },
        setFilterParameter: (name, value) => {
          dispatch(filtersActions.setFilterParameter(namespace, name, value));
        },
      },
    })
  )(MapController);
}
