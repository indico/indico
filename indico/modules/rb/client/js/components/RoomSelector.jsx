// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getLocationsURL from 'indico-url:rb.locations';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Button, Dropdown, Grid, Icon, List, Message, Segment} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import SpriteImage from './SpriteImage';

import './RoomSelector.module.scss';

const fetchLocations = async () => {
  let response;
  try {
    response = await indicoAxios.get(getLocationsURL());
  } catch (error) {
    handleAxiosError(error);
    return;
  }

  return camelizeKeys(response);
};

class RoomSelector extends React.Component {
  static propTypes = {
    onChange: PropTypes.func.isRequired,
    onFocus: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired,
    value: PropTypes.array.isRequired,
    disabled: PropTypes.bool,
    readOnly: PropTypes.bool,
    renderRoomActions: PropTypes.func,
  };

  static defaultProps = {
    disabled: false,
    readOnly: false,
    renderRoomActions: () => {},
  };

  state = {
    isFetchingLocations: false,
    locations: [],
    selectedLocation: null,
    selectedRoom: null,
  };

  componentDidMount() {
    // eslint-disable-next-line react/no-did-mount-set-state
    this.setState({isFetchingLocations: true}, async () => {
      const {data: locations} = await fetchLocations();
      this.setState({
        locations,
        isFetchingLocations: false,
        selectedLocation: locations.length === 1 ? locations[0] : null,
      });
    });
  }

  shouldComponentUpdate(nextProps, nextState) {
    const {disabled: prevDisabled, readOnly: prevReadOnly, value: prevValue} = this.props;
    const {disabled, readOnly, value} = nextProps;
    return (
      nextState !== this.state ||
      disabled !== prevDisabled ||
      readOnly !== prevReadOnly ||
      !_.isEqual(value, prevValue)
    );
  }

  removeItem = room => {
    const {onChange, value} = this.props;
    const newRooms = value.filter(item => item.id !== room.id);
    this.setTouched();
    onChange(newRooms);
  };

  renderRoomItem = room => {
    const {disabled, readOnly, renderRoomActions} = this.props;

    return (
      <List.Item key={room.id}>
        <div className="image-wrapper" style={{width: 55, height: 25}}>
          <SpriteImage pos={room.spritePosition} width="100%" height="100%" fillVertical />
        </div>
        <List.Content>
          <List.Header>{room.fullName}</List.Header>
        </List.Content>
        <List.Content styleName="room-actions">
          {renderRoomActions(room)}
          {!readOnly && (
            <Icon
              name="remove"
              disabled={disabled}
              onClick={() => !disabled && this.removeItem(room)}
            />
          )}
        </List.Content>
      </List.Item>
    );
  };

  setTouched = () => {
    // pretend focus+blur to mark the field as touched in case an action changes
    // the data without actually involving focus and blur of a form element
    const {onFocus, onBlur} = this.props;
    onFocus();
    onBlur();
  };

  render() {
    const {onChange, onFocus, onBlur, readOnly, value: rooms} = this.props;
    const {locations, selectedLocation, selectedRoom, isFetchingLocations} = this.state;
    const locationOptions = locations.map(location => ({text: location.name, value: location.id}));
    let roomOptions = [];
    if (selectedLocation) {
      roomOptions = selectedLocation.rooms
        .filter(room => rooms.findIndex(item => item.id === room.id) === -1)
        .map(room => ({text: room.fullName, value: room.id}));
    }

    return (
      <Grid styleName="room-selector">
        <Grid.Row>
          {!readOnly && (
            <>
              <Grid.Column width={5}>
                <Dropdown
                  placeholder={Translate.string('Location')}
                  options={locationOptions}
                  value={selectedLocation && selectedLocation.id}
                  loading={isFetchingLocations}
                  onChange={(event, data) => {
                    const selected = locations.find(loc => loc.id === data.value);
                    this.setState({selectedLocation: selected});
                  }}
                  onFocus={onFocus}
                  onBlur={onBlur}
                  fluid
                  search
                  selection
                />
              </Grid.Column>
              <Grid.Column width={9}>
                <Dropdown
                  placeholder={Translate.string('Room')}
                  disabled={!selectedLocation}
                  options={roomOptions}
                  value={selectedRoom && selectedRoom.id}
                  onChange={(event, data) => {
                    const selected = selectedLocation.rooms.find(room => room.id === data.value);
                    this.setState({selectedRoom: selected});
                  }}
                  onFocus={onFocus}
                  onBlur={onBlur}
                  fluid
                  search
                  selection
                />
              </Grid.Column>
              <Grid.Column width={2}>
                <Button
                  floated="right"
                  icon="plus"
                  type="button"
                  disabled={!selectedRoom}
                  onClick={() => {
                    this.setState({selectedRoom: null});
                    onChange([...rooms, selectedRoom]);
                  }}
                  primary
                />
              </Grid.Column>
            </>
          )}
        </Grid.Row>
        <Grid.Row styleName="selected-rooms-row">
          <Grid.Column>
            {rooms.length !== 0 && (
              <Segment>
                <List styleName="rooms-list" verticalAlign="middle" relaxed>
                  {rooms.map(this.renderRoomItem)}
                </List>
              </Segment>
            )}
            {rooms.length === 0 && (
              <Message info>
                <Translate>There are no rooms selected.</Translate>
              </Message>
            )}
          </Grid.Column>
        </Grid.Row>
      </Grid>
    );
  }
}

/**
 * Like `FinalField` but for a `RoomSelector`.
 */
export default function FinalRoomSelector({name, ...rest}) {
  return <FinalField name={name} component={RoomSelector} isEqual={_.isEqual} {...rest} />;
}

FinalRoomSelector.propTypes = {
  name: PropTypes.string.isRequired,
  readOnly: PropTypes.bool,
};

FinalRoomSelector.defaultProps = {
  readOnly: false,
};
