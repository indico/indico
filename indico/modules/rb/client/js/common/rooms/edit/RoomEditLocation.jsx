// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form, Header, Tab} from 'semantic-ui-react';

import {FinalInput, parsers as p, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

export default function RoomEditLocation({active}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Location</Translate>
      </Header>
      <FinalInput
        fluid
        name="verbose_name"
        label={Translate.string('Name')}
        required={false}
        nullIfEmpty
      />
      <Form.Group widths="four">
        <Form.Field width={8}>
          <FinalInput name="site" label={Translate.string('Site')} />
        </Form.Field>
        <FinalInput name="building" label={Translate.string('Building')} required />
        <FinalInput name="floor" label={Translate.string('Floor')} required />
        <FinalInput name="number" label={Translate.string('Number')} required />
      </Form.Group>
      <Form.Group widths="equal">
        <FinalInput
          fluid
          type="number"
          name="surface_area"
          label={Translate.string('Surface Area (m²)')}
          min="0"
          validate={v.optional(v.min(0))}
        />
        <FinalInput
          fluid
          type="text"
          name="latitude"
          label={Translate.string('Latitude')}
          parse={f => p.number(f, false)}
          validate={v.optional(v.number())}
        />
        <FinalInput
          fluid
          type="text"
          name="longitude"
          label={Translate.string('Longitude')}
          parse={f => p.number(f, false)}
          validate={v.optional(v.number())}
        />
      </Form.Group>
    </Tab.Pane>
  );
}

RoomEditLocation.propTypes = {
  active: PropTypes.bool,
};

RoomEditLocation.defaultProps = {
  active: true,
};
