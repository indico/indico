// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import locationsURL from 'indico-url:event_management.api_locations';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown, Form, Icon, Popup} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import './LocationField.module.scss';

const EMPTY_LOCATION_VALUE = {
  venue_id: null,
  venue_name: '',
  room_id: null,
  room_name: '',
  address: '',
};

const processLocations = (locations, value) => {
  if (!locations.length) {
    return [[], []];
  }
  const venues = locations.map(({id, name}) => ({key: id, text: name, value: id}));
  const rooms = locations.flatMap(location => [
    {
      key: `_loc:${location.id}`,
      text: location.name,
      as: Dropdown.Header,
      disabled: true,
    },
    ...location.rooms.map(({id, fullName}) => ({
      key: id,
      text: fullName,
      value: id,
    })),
  ]);
  if (value.venue_name && !value.venue_id) {
    venues.push({
      key: 'custom',
      text: value.venue_name,
      value: value.venue_name,
      content: Translate.string('Custom venue: "{venue}"', {venue: value.venue_name}),
    });
  }
  if (value.room_name && !value.room_id) {
    rooms.push({
      key: 'custom',
      text: value.room_name,
      value: value.room_name,
      content: Translate.string('Custom room: "{room}"', {room: value.room_name}),
    });
  }
  return [venues, rooms];
};

export default function LocationField({
  value,
  onChange,
  disabled,
  required,
  editAddress,
  locationParent,
}) {
  const {data, loading} = useIndicoAxios(locationsURL(), {camelize: true});
  const locationsEnabled = data?.enabled || false;
  const locations = data?.locations || [];
  const [venues, rooms] = processLocations(locations, value);

  const handleChangeVenue = (evt, {value: locationId}) => {
    if (typeof locationId === 'string') {
      onChange({
        ...value,
        venue_id: null,
        venue_name: locationId,
        room_id: null,
        room_name: value.room_id ? '' : value.room_name,
      });
      return;
    }
    onChange({
      ...value,
      venue_id: locationId,
      venue_name: locations.find(l => l.id === locationId).name,
      room_id: null,
      room_name: value.room_id ? '' : value.room_name,
    });
  };

  const handleChangeRoom = (evt, {value: roomId}) => {
    if (typeof roomId === 'string') {
      onChange({
        ...value,
        room_id: null,
        room_name: roomId,
      });
      return;
    }
    const location = locations.find(l => l.rooms.some(r => r.id === roomId));
    onChange({
      ...value,
      venue_id: location.id,
      venue_name: location.name,
      room_id: roomId,
      room_name: location.rooms.find(r => r.id === roomId).fullName,
    });
  };

  const makeOnChange =
    key =>
    (evt, {value: fieldValue}) =>
      onChange({...value, [key]: fieldValue});

  return (
    <>
      {locationsEnabled || loading ? (
        <Form.Group widths="equal">
          <Form.Select
            styleName="venue-dropdown"
            placeholder={Translate.string('Venue')}
            disabled={disabled || value.inheriting}
            required={required && !value.inheriting}
            clearable={!required}
            options={venues}
            value={value.venue_id || value.venue_name}
            onChange={handleChangeVenue}
            loading={loading}
            selectOnBlur={false}
            search
            allowAdditions
            additionLabel={`${Translate.string('Just use')} `}
          />
          <Form.Select
            styleName="room-dropdown"
            placeholder={Translate.string('Room')}
            disabled={disabled || value.inheriting}
            required={required && !value.inheriting}
            clearable={!required}
            options={rooms}
            value={value.room_id || value.room_name}
            onChange={handleChangeRoom}
            loading={loading}
            selectOnBlur={false}
            search
            allowAdditions
            additionLabel={`${Translate.string('Just use')} `}
          />
        </Form.Group>
      ) : (
        <Form.Group widths="equal">
          <Form.Input
            styleName="venue-field"
            placeholder={Translate.string('Venue')}
            value={value.venue_name || ''}
            onChange={makeOnChange('venue_name')}
            disabled={disabled || value.inheriting}
            required={required}
          />
          <Form.Input
            styleName="room-field"
            placeholder={Translate.string('Room')}
            value={value.room_name || ''}
            onChange={makeOnChange('room_name')}
            disabled={disabled || value.inheriting}
            required={required}
          />
        </Form.Group>
      )}
      {editAddress && (
        <Form.TextArea
          placeholder={Translate.string('Address')}
          value={value.address || ''}
          onChange={makeOnChange('address')}
          disabled={disabled || value.inheriting}
          required={required}
        />
      )}
      {locationParent && (
        <Form.Group>
          <Form.Checkbox
            label={Translate.string('Use default')}
            checked={value.inheriting}
            onChange={(evt, {checked}) =>
              onChange(
                checked
                  ? {...locationParent.location_data, inheriting: true}
                  : {...EMPTY_LOCATION_VALUE, inheriting: false}
              )
            }
            disabled={disabled}
          />
          <Popup
            trigger={<Icon color="grey" name="info circle" />}
            content={
              value.inheriting
                ? Translate.string("Using default location from '{title}' ({type})", {
                    title: locationParent.title,
                    type: locationParent.type,
                  })
                : Translate.string('Using custom location')
            }
          />
        </Form.Group>
      )}
    </>
  );
}

LocationField.propTypes = {
  value: PropTypes.shape({
    venue_id: PropTypes.number,
    venue_name: PropTypes.string,
    room_id: PropTypes.number,
    room_name: PropTypes.string,
    address: PropTypes.string,
    inheriting: PropTypes.bool,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  editAddress: PropTypes.bool,
  locationParent: PropTypes.shape({
    title: PropTypes.string,
    type: PropTypes.string,
    location_data: PropTypes.shape({
      venue_id: PropTypes.number,
      venue_name: PropTypes.string,
      room_id: PropTypes.number,
      room_name: PropTypes.string,
      address: PropTypes.string,
    }),
  }),
};

LocationField.defaultProps = {
  disabled: false,
  required: false,
  editAddress: true,
  locationParent: null,
};

export function FinalLocationField({name, ...rest}) {
  return <FinalField name={name} component={LocationField} isEqual={_.isEqual} {...rest} />;
}

FinalLocationField.propTypes = {
  name: PropTypes.string.isRequired,
};
