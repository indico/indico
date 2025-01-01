// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import roomImageURL from 'indico-url:rb.room_photo';

import PropTypes from 'prop-types';
import React from 'react';
import {Dimmer, Grid, Header, Icon, Image, Loader, Modal, Popup} from 'semantic-ui-react';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import {formatLatLon} from '../common/map/util';

import RoomFeatureEntry from './RoomFeatureEntry';
import SpriteImage from './SpriteImage';

import styles from './RoomBasicDetails.module.scss';

function RoomFeaturesBox({room: {features}}) {
  if (!features.length) {
    return null;
  }
  return (
    <div styleName="feature-box">
      <div styleName="feature-entries">
        {features.map(feature => (
          <RoomFeatureEntry
            key={feature.name}
            feature={feature}
            color="teal"
            size="large"
            classes={styles['feature-entry']}
          />
        ))}
      </div>
    </div>
  );
}

RoomFeaturesBox.propTypes = {
  room: PropTypes.shape({
    features: PropTypes.array.isRequired,
  }).isRequired,
};

function AnnotatedIcon({name, text}) {
  return <Popup content={text} trigger={<Icon name={name} />} />;
}

AnnotatedIcon.propTypes = {
  name: PropTypes.string.isRequired,
  text: PropTypes.string.isRequired,
};

export default class RoomBasicDetails extends React.PureComponent {
  static propTypes = {
    room: PropTypes.object.isRequired,
  };

  state = {
    imageModalOpen: false,
    imageLoaded: false,
  };

  renderImage() {
    const {room} = this.props;
    const {imageModalOpen, imageLoaded} = this.state;
    const isClickable = room.hasPhoto;
    const spriteImage = (
      <SpriteImage
        styleName="clickable"
        pos={room.spritePosition}
        height="100%"
        width="100%"
        fillVertical
        onClick={isClickable ? () => this.setState({imageModalOpen: true}) : undefined}
      />
    );
    if (isClickable) {
      return (
        <>
          <Modal
            closeIcon
            open={imageModalOpen}
            onClose={() => this.setState({imageModalOpen: false, imageLoaded: false})}
          >
            <Modal.Content image styleName="photo-dimmer">
              <Dimmer.Dimmable styleName="photo-dimmable-width">
                <Dimmer active={!imageLoaded} inverted>
                  <Loader />
                </Dimmer>
                <Image
                  styleName="photo-width"
                  wrapped
                  onLoad={() => this.setState({imageLoaded: true})}
                  src={roomImageURL({room_id: room.id})}
                />
              </Dimmer.Dimmable>
            </Modal.Content>
          </Modal>
          <div styleName="image-container clickable">
            {spriteImage}
            <RoomFeaturesBox room={room} />
          </div>
        </>
      );
    } else {
      return (
        <div styleName="image-container">
          {spriteImage}
          <RoomFeaturesBox room={room} />
        </div>
      );
    }
  }

  render() {
    const {room} = this.props;
    const {
      ownerName: owner,
      latitude,
      longitude,
      division,
      mapURL,
      locationName: location,
      surfaceArea: surface,
      capacity,
      telephone,
      fullName: name,
      site,
    } = room;
    return (
      <Grid columns={2} stackable>
        <Grid.Column textAlign="center" styleName="photo-column">
          {this.renderImage()}
        </Grid.Column>
        <Grid.Column styleName="data-column">
          <Header>
            {name}
            <Header.Subheader>{division}</Header.Subheader>
          </Header>
          <ul styleName="room-basic-details">
            <li className="has-icon">
              {location && (
                <>
                  <AnnotatedIcon name="map pin" text={Translate.string('Location')} />
                  {location}
                </>
              )}
            </li>
            <li className="has-icon">
              {site && (
                <>
                  <AnnotatedIcon
                    name="street view"
                    text={Translate.string('Site', 'Building site/location')}
                  />
                  {site}
                </>
              )}
            </li>
            <li className="has-icon">
              <AnnotatedIcon name="id badge outline" text={Translate.string('Room Owner')} />
              {owner}
            </li>
            <li className="has-icon">
              {telephone && (
                <>
                  <AnnotatedIcon name="phone" text={Translate.string('Phone number')} />
                  {telephone}
                </>
              )}
            </li>
            <li className="has-icon">
              {capacity && (
                <>
                  <AnnotatedIcon name="users" text={Translate.string('Capacity')} />
                  <PluralTranslate count={capacity}>
                    <Singular>
                      1{' '}
                      <Param name="label" wrapper={<label />}>
                        seat
                      </Param>
                    </Singular>
                    <Plural>
                      <Param name="count" value={capacity} />{' '}
                      <Param name="label" wrapper={<label />}>
                        seats
                      </Param>
                    </Plural>
                  </PluralTranslate>
                </>
              )}
            </li>
            <li className="has-icon">
              {surface && (
                <>
                  <AnnotatedIcon name="cube" text={Translate.string('Surface Area')} />
                  {surface} <label>m²</label>
                </>
              )}
            </li>
            <li className="has-icon">
              {latitude && (
                <>
                  <AnnotatedIcon
                    name="location arrow"
                    text={Translate.string('Geographical Coordinates')}
                  />
                  <a target="_blank" rel="noopener noreferrer" href={mapURL}>
                    {formatLatLon(latitude, longitude)}
                  </a>
                </>
              )}
            </li>
          </ul>
        </Grid.Column>
      </Grid>
    );
  }
}
