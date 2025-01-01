// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Leaflet from 'leaflet';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {FeatureGroup, Map, Rectangle, TileLayer, Tooltip, ZoomControl} from 'react-leaflet';
import {EditControl} from 'react-leaflet-draw';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Button, Form, Header, Modal} from 'semantic-ui-react';

import {FinalCheckbox, FinalInput, FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {selectors as configSelectors} from '../../common/config';
import {selectors as mapSelectors, actions as mapActions} from '../../common/map';

import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import './MapAreasPage.module.scss';

Leaflet.EditToolbar.Delete.include({
  removeAllLayers: false,
});

const DEFAULT_CENTER = [46.233832398, 6.053166454];

class MapAreasPage extends React.Component {
  static propTypes = {
    tileServerURL: PropTypes.string.isRequired,
    areas: PropTypes.arrayOf(PropTypes.object).isRequired,
    actions: PropTypes.exact({
      createMapArea: PropTypes.func.isRequired,
      updateMapAreas: PropTypes.func.isRequired,
      deleteMapAreas: PropTypes.func.isRequired,
      fetchMapAreas: PropTypes.func.isRequired,
    }).isRequired,
  };

  constructor(props) {
    super(props);

    this.map = null;
    this.featureGroup = null;
  }

  state = {
    areaProps: null,
    suppressClick: false,
  };

  componentDidMount() {
    const {
      actions: {fetchMapAreas},
    } = this.props;
    fetchMapAreas();
    // rerender is required here because only at this point this.map
    // refers to the actual map element which is then necessary in this.drawAreas
    this.forceUpdate();
  }

  setMapAreaRef = ref => {
    this.map = ref;
  };

  setFeatureGroupRef = ref => {
    this.featureGroup = ref;
  };

  createNewArea = evt => {
    const {
      layerType,
      layer: {
        _bounds: {_northEast: northEast, _southWest: southWest},
      },
    } = evt;

    if (layerType !== 'rectangle') {
      return;
    }

    this.setState({
      areaProps: {bounds: {northEast, southWest}},
    });

    if (this.featureGroup) {
      // this is necessary here so that we don't end up with
      // the initial layer being still visible on the map
      this.featureGroup.leafletElement.eachLayer(layer => {
        const {
          options: {id},
        } = layer;
        if (id === undefined) {
          this.featureGroup.leafletElement.removeLayer(layer);
        }
      });
    }
  };

  editArea = evt => {
    if (!Object.keys(evt.layers._layers).length) {
      return;
    }

    const {
      actions: {updateMapAreas},
    } = this.props;
    const editedAreas = [];

    evt.layers.eachLayer(({options: {id}, _bounds}) => {
      const {_southWest: southWest, _northEast: northEast} = _bounds;
      editedAreas.push({
        id,
        bounds: {southWest, northEast},
      });
    });

    updateMapAreas(editedAreas);
  };

  deleteMapAreas = evt => {
    if (!Object.keys(evt.layers._layers).length) {
      return;
    }

    const {
      actions: {deleteMapAreas},
    } = this.props;
    const deletedAreas = [];

    evt.layers.eachLayer(({options: {id}}) => {
      deletedAreas.push(id);
    });

    deleteMapAreas(deletedAreas);
  };

  drawAreas = () => {
    if (this.map === null) {
      return null;
    }

    const {areas} = this.props;
    return areas.map(this._drawArea);
  };

  _drawArea = ({
    id,
    is_default: isDefault,
    name,
    top_left_latitude: topLeftLat,
    top_left_longitude: topLeftLng,
    bottom_right_latitude: bottomRightLat,
    bottom_right_longitude: bottomRightLng,
  }) => {
    const southWest = [topLeftLat, topLeftLng];
    const northEast = [bottomRightLat, bottomRightLng];
    const latLngBounds = new Leaflet.LatLngBounds([southWest, northEast]);
    const center = this.map.leafletElement.latLngToContainerPoint(latLngBounds.getCenter());
    const bottomRight = this.map.leafletElement.latLngToContainerPoint(latLngBounds.getSouthEast());
    const onAreaClick = () => {
      const {suppressClick} = this.state;
      if (suppressClick) {
        return;
      }

      this.setState({
        areaProps: {
          bounds: {
            southWest: latLngBounds.getSouthWest(),
            northEast: latLngBounds.getNorthEast(),
          },
          id,
          isDefault,
          name,
        },
      });
    };

    return (
      <Rectangle
        key={`${name}-${center.x}-${center.y}`}
        bounds={[southWest, northEast]}
        name={name}
        isDefault={isDefault}
        onClick={onAreaClick}
        id={id}
      >
        <Tooltip
          offset={[bottomRight.x - center.x, bottomRight.y - center.y]}
          direction="bottom"
          sticky
          permanent
          interactive
        >
          <>
            {name}
            {isDefault && <span className="area-default">★</span>}
          </>
        </Tooltip>
      </Rectangle>
    );
  };

  onSubmit = async data => {
    const {
      actions: {createMapArea, updateMapAreas},
    } = this.props;
    const {
      areaProps: {id},
    } = this.state;

    if (id === undefined) {
      await createMapArea(data);
    } else {
      await updateMapAreas([{...data, id}]);
    }

    this.setState({areaProps: null});
  };

  renderModalForm = () => {
    const {areaProps} = this.state;
    if (!areaProps) {
      return null;
    }

    const {id, bounds, name, isDefault} = areaProps;
    return (
      <FinalForm
        onSubmit={this.onSubmit}
        render={this.renderForm}
        subscription={{}}
        initialValues={{
          name: id === undefined ? null : name,
          bounds,
          default: isDefault,
        }}
      />
    );
  };

  renderForm = ({handleSubmit}) => {
    const {
      areaProps: {id},
    } = this.state;
    const isNewArea = id === undefined;

    return (
      <Modal onClose={() => this.setState({areaProps: null})} closeIcon open>
        <Modal.Header>
          {isNewArea ? <Translate>Create new area</Translate> : <Translate>Update area</Translate>}
        </Modal.Header>
        <Modal.Content>
          <Form id="map-area-form" onSubmit={handleSubmit}>
            <Form.Group>
              <FinalInput
                name="name"
                label={Translate.string('Name of the area')}
                autoFocus
                required
              />
            </Form.Group>
            <Form.Group>
              <FinalCheckbox
                name="default"
                label={Translate.string('Default map area')}
                showAsToggle
              />
            </Form.Group>
            <Form.Group>
              <FinalInput
                name="bounds.southWest.lat"
                type="number"
                label={Translate.string('SW Latitude')}
                step="0.00000000000001"
                required
              />
              <FinalInput
                name="bounds.southWest.lng"
                type="number"
                label={Translate.string('SW Longitude')}
                step="0.00000000000001"
                required
              />
            </Form.Group>
            <Form.Group>
              <FinalInput
                name="bounds.northEast.lat"
                label={Translate.string('NE Latitude')}
                step="0.00000000000001"
                type="number"
                required
              />
              <FinalInput
                name="bounds.northEast.lng"
                label={Translate.string('NE Longitude')}
                step="0.00000000000001"
                type="number"
                required
              />
            </Form.Group>
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <FinalSubmitButton
            form="map-area-form"
            label={isNewArea ? Translate.string('Create') : Translate.string('Update')}
            primary
          />
          <Button onClick={() => this.setState({areaProps: null})}>
            <Translate>Cancel</Translate>
          </Button>
        </Modal.Actions>
      </Modal>
    );
  };

  render() {
    const {tileServerURL, areas} = this.props;
    const defaultArea = areas.find(area => area.is_default);
    const bounds = defaultArea
      ? new Leaflet.LatLngBounds([
          [defaultArea.top_left_latitude, defaultArea.top_left_longitude],
          [defaultArea.bottom_right_latitude, defaultArea.bottom_right_longitude],
        ])
      : null;
    const eventHandlers = ['draw', 'edit', 'delete'].reduce((acc, eventName) => {
      eventName = _.capitalize(eventName);
      return {
        ...acc,
        [`on${eventName}Start`]: () => this.setState({suppressClick: true}),
        [`on${eventName}Stop`]: () => this.setState({suppressClick: false}),
      };
    }, {});
    return (
      <>
        <Header as="h2">
          <Translate>Map Areas</Translate>
        </Header>
        <div styleName="areas-map-container">
          <Map
            ref={this.setMapAreaRef}
            center={bounds ? bounds.getCenter() : DEFAULT_CENTER}
            onZoomEnd={() => {
              const {suppressClick} = this.state;
              if (!suppressClick) {
                this.forceUpdate();
              }
            }}
            zoomControl={false}
            zoom={14}
          >
            <TileLayer
              attribution='© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
              minZoom="14"
              maxZoom="20"
              url={tileServerURL}
            />
            <FeatureGroup ref={this.setFeatureGroupRef}>
              <EditControl
                position="topleft"
                onCreated={this.createNewArea}
                onEdited={this.editArea}
                onDeleted={this.deleteMapAreas}
                draw={{
                  marker: false,
                  circle: false,
                  polygon: false,
                  polyline: false,
                  circlemarker: false,
                }}
                {...eventHandlers}
              />
              {areas.length !== 0 && this.drawAreas()}
            </FeatureGroup>
            <ZoomControl position="bottomleft" />
          </Map>
        </div>
        {this.renderModalForm()}
      </>
    );
  }
}

export default connect(
  state => ({
    areas: mapSelectors.getMapAreas(state),
    tileServerURL: configSelectors.getTileServerURL(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        createMapArea: mapActions.createMapArea,
        deleteMapAreas: mapActions.deleteMapAreas,
        updateMapAreas: mapActions.updateMapAreas,
        fetchMapAreas: mapActions.fetchAreas,
      },
      dispatch
    ),
  })
)(MapAreasPage);
