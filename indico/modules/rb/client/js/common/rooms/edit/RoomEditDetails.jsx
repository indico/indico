// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form, Header, Tab} from 'semantic-ui-react';

import {FinalPrincipal} from 'indico/react/components';
import {FinalInput, FinalTextArea, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

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
          min="1"
          validate={v.min(1)}
          required
        />
        <FinalInput fluid name="division" label={Translate.string('Division')} />
      </Form.Group>
      <FinalTextArea
        name="comments"
        label={Translate.string('Comments')}
        description={Translate.string('You may use Markdown for formatting.')}
      />
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
