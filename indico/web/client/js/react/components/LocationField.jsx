// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import locationsURL from 'indico-url:rb.locations'; // TODO replace this with proper endpoint

import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown, Form} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import './LocationField.module.scss';

export default function LocationField({
  value,
  onChange,
  disabled,
  required,
  editAddress,
  allowLocationInheritance,
}) {
  const {data: locations, loading} = useIndicoAxios(locationsURL(), {camelize: true}); // TODO check if we need to handle 404s if RB is disabled

  const venues = locations?.map(({id, name}) => ({key: id, text: name, value: id})) || [];
  const rooms =
    locations?.flatMap(location => [
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
    ]) || [];
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

  return (
    <>
      <Form.Group widths="equal">
        <Form.Select
          placeholder={Translate.string('Venue')}
          disabled={disabled || value.use_default}
          required={required && !value.use_default}
          clearable={!required}
          options={venues}
          value={value.venue_id || value.venue_name}
          onChange={(_, {value: locationId}) => {
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
          }}
          loading={loading}
          selectOnBlur={false}
          search
          allowAdditions
        />
        <Form.Select
          styleName="room-dropdown"
          placeholder={Translate.string('Room')}
          disabled={disabled || value.use_default}
          required={required && !value.use_default}
          clearable={!required}
          options={rooms}
          value={value.room_id || value.room_name}
          onChange={(_, {value: roomId}) => {
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
          }}
          loading={loading}
          selectOnBlur={false}
          search
          allowAdditions
        />
      </Form.Group>
      {editAddress && (
        <Form.TextArea
          placeholder={Translate.string('Address')}
          value={value.address || ''}
          onChange={(_, {value: address}) => onChange({...value, address})}
          disabled={disabled || value.use_default}
          required={required && !value.use_default}
        />
      )}
      {allowLocationInheritance && (
        <Form.Checkbox
          label={Translate.string('Use default')}
          checked={value.use_default}
          onChange={(_, {checked}) =>
            onChange(checked ? {use_default: true} : {...value, use_default: false})
          }
          disabled={disabled}
        />
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
    use_default: PropTypes.bool,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  editAddress: PropTypes.bool,
  allowLocationInheritance: PropTypes.bool,
};

LocationField.defaultProps = {
  disabled: false,
  required: false,
  editAddress: true,
  allowLocationInheritance: true,
};

export function FinalLocationField({name, ...rest}) {
  return <FinalField name={name} component={LocationField} {...rest} />;
}

FinalLocationField.propTypes = {
  name: PropTypes.string.isRequired,
};
