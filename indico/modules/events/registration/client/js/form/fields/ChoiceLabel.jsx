// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

export default function ChoiceLabel({choice}) {
  let warning = null;
  if (choice._deleted) {
    warning = (
      <Translate>
        The currently chosen option is not available anymore. If you unselect it you won't be able
        to choose it back.
      </Translate>
    );
  } else if (choice._modified) {
    warning = choice.price ? (
      <Translate>
        The currently chosen option has been modified. If you unselect it you may not be able to
        select it again for the same price.
      </Translate>
    ) : (
      <Translate>
        The currently chosen option has been modified. If you unselect it you may not be able to
        select it again.
      </Translate>
    );
  } else {
    return choice.caption;
  }
  return (
    <>
      {choice.caption}{' '}
      <Popup trigger={<Icon name="warning sign" color="orange" />}>{warning}</Popup>
    </>
  );
}

ChoiceLabel.propTypes = {
  choice: PropTypes.shape({
    caption: PropTypes.string.isRequired,
    price: PropTypes.number,
    _deleted: PropTypes.bool,
    _modified: PropTypes.bool,
  }).isRequired,
};
