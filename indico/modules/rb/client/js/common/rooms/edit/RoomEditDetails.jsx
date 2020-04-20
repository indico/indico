// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Form, Header, Tab} from 'semantic-ui-react';
import React from 'react';
import PropTypes from 'prop-types';
import {FinalPrincipal} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {FinalInput, FinalTextArea, validators as v} from 'indico/react/forms';

function RoomEditDetails({active, favoriteUsersController}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Contact</Translate>
      </Header>
      <FinalPrincipal
        name="owner"
        favoriteUsersController={favoriteUsersController}
        label={Translate.string('Owner')}
        hideErrorPopup={!active}
        allowNull
        required
      />
      <Form.Group widths="equal">
        <FinalInput
          fluid
          name="key_location"
          label={Translate.string('Where is the key?')}
          hideErrorPopup={!active}
        />
        <FinalInput
          fluid
          name="telephone"
          label={Translate.string('Telephone')}
          hideErrorPopup={!active}
        />
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
          validate={v.min(1)}
          hideErrorPopup={!active}
          required
        />
        <FinalInput
          fluid
          name="division"
          label={Translate.string('Division')}
          hideErrorPopup={!active}
          required
        />
      </Form.Group>
      <FinalTextArea
        name="comments"
        label={Translate.string('Comments')}
        hideErrorPopup={!active}
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

export default RoomEditDetails;
