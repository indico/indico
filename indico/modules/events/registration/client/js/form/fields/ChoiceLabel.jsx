// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

export default function ChoiceLabel({paid, management, choice}) {
  let modWarning = null;
  let paymentWarning = null;
  // warning about modified/removed choice
  if (choice._deleted) {
    modWarning = (
      <Translate>
        The currently chosen option is not available anymore. If you unselect it you won't be able
        to choose it back.
      </Translate>
    );
  } else if (choice._modified) {
    modWarning = choice.price ? (
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
  }
  // warning about price changes
  if (paid && !management) {
    paymentWarning = (
      <Translate>This option could trigger a price change and has been blocked.</Translate>
    );
  } else if (paid) {
    paymentWarning = <Translate>Choosing this option will result in a price change.</Translate>;
  }
  if (!modWarning && !paymentWarning) {
    return choice.caption;
  }
  return (
    <>
      {choice.caption}{' '}
      {modWarning && (
        <Popup trigger={<Icon name="warning sign" color="orange" />}>{modWarning}</Popup>
      )}
      {modWarning && paymentWarning && ' '}
      {paymentWarning && (
        <Popup trigger={<Icon name="warning sign" color="orange" />}>{paymentWarning}</Popup>
      )}
    </>
  );
}

ChoiceLabel.propTypes = {
  paid: PropTypes.bool.isRequired,
  management: PropTypes.bool.isRequired,
  choice: PropTypes.shape({
    caption: PropTypes.string.isRequired,
    price: PropTypes.number,
    _deleted: PropTypes.bool,
    _modified: PropTypes.bool,
  }).isRequired,
};
