// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Form, Header, Tab} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import {FinalPrincipal} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {FinalInput, FinalTextArea} from 'indico/react/forms';

export default function RoomEditDetails({active, favoriteUsersController}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Contact</Translate>
      </Header>
      <FinalPrincipal
        name="owner"
        favoriteUsersController={favoriteUsersController}
        label={Translate.string('Owner')}
        allowNull
        required
      />
      <Form.Group widths="equal">
        <FinalInput fluid name="key_location" label={Translate.string('Where is the key?')} />
        <FinalInput fluid name="telephone" label={Translate.string('Telephone')} />
      </Form.Group>
      <Header>
        <Translate>Information</Translate>
      </Header>
      <Form.Group widths="equal">
        <FinalInput
          fluid
          type="number"
          name="capacity"
          label={Translate.string('Capacity')}
          required
        />
        <FinalInput fluid name="division" label={Translate.string('Division')} required />
      </Form.Group>
      <FinalTextArea name="comments" label={Translate.string('Comments')} />
    </Tab.Pane>
  );
}

RoomEditDetails.propTypes = {
  active: PropTypes.bool,
  favoriteUsersController: PropTypes.array.isRequired,
};

RoomEditDetails.defaultProps = {
  active: true,
};
