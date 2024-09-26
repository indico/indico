// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import locationsURL from 'indico-url:event_management.api_locations';

import React from 'react';
import {Dropdown, Form, Icon, Popup} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import './LocationField.module.scss';

interface LocationType {
  id: number;
  name: string;
  rooms: {id: number; fullName: string}[];
}

const processLocations = (locations: LocationType[], value) => {
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

interface LocationFieldProps {
  disabled?: boolean;
  required?: boolean;
  editAddress?: boolean;
  parent?: {
    title: string;
    type: string;
    location_data?: {
      venue_id: number;
      venue_name: string;
      room_id: number;
      room_name: string;
      address: string;
    };
  };
}

interface LocationValueType {
  venue_id: number;
  venue_name: string;
  room_id: number;
  room_name: string;
  address: string;
  use_default: boolean;
}

interface LocationFieldComponentProps extends LocationFieldProps {
  value: LocationValueType;
  onChange: (value: LocationValueType) => void;
}

export default function LocationField({value, onChange, disabled = false, required = false, editAddress = true, parent = null}: LocationFieldComponentProps) {
  const {data, loading} = useIndicoAxios(locationsURL(), {camelize: true});
  const locationsEnabled = data?.enabled || false;
  const locations = data?.locations || [];
  const [venues, rooms] = processLocations(locations, value);

  const handleChangeVenue = (_, {value: locationId}) => {
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

  const handleChangeRoom = (_, {value: roomId}) => {
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

  const makeOnChange = key => (_, {value: fieldValue}) => onChange({...value, [key]: fieldValue});

  return (
    <>
      {locationsEnabled || loading ? (
        <Form.Group widths="equal">
          <Form.Select
            styleName="venue-dropdown"
            placeholder={Translate.string('Venue')}
            disabled={disabled || value.use_default}
            required={required && !value.use_default}
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
            disabled={disabled || value.use_default}
            required={required && !value.use_default}
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
            disabled={disabled || value.use_default}
            required={required}
          />
          <Form.Input
            styleName="room-field"
            placeholder={Translate.string('Room')}
            value={value.room_name || ''}
            onChange={makeOnChange('room_name')}
            disabled={disabled || value.use_default}
            required={required}
          />
        </Form.Group>
      )}
      {editAddress && (
        <Form.TextArea
          placeholder={Translate.string('Address')}
          value={value.address || ''}
          onChange={makeOnChange('address')}
          disabled={disabled || value.use_default}
          required={required}
        />
      )}
      {parent && (
        <Form.Group>
          <Form.Checkbox
            label={Translate.string('Use default')}
            checked={value.use_default}
            onChange={(_, {checked}) =>
              onChange(
                checked
                  ? {...(parent.location_data || {}), use_default: true}
                  : {...value, use_default: false}
              )
            }
            disabled={disabled}
          />
          <Popup
            trigger={<Icon color="grey" name="info circle" />}
            content={
              value.use_default
                ? Translate.string("Using default location from '{title}' ({type})", {
                    title: parent.title,
                    type: parent.type,
                  })
                : Translate.string('Using custom location')
            }
          />
        </Form.Group>
      )}
    </>
  );
}

interface FinalLocationFieldProps extends LocationFieldProps {
  name: string;
}

export function FinalLocationField({name, ...rest}: FinalLocationFieldProps) {
  return <FinalField name={name} component={LocationField} {...rest} />;
}
