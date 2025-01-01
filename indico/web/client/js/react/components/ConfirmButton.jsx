// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef, useState} from 'react';
import {Button, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

export default function ConfirmButton({onClick, delay, popupContent, confirmOverrides, ...rest}) {
  const countdown = useRef(null);
  const [confirming, setConfirming] = useState(0);

  const resetConfirming = () => {
    if (countdown.current) {
      clearInterval(countdown.current);
      countdown.current = null;
    }
    if (confirming !== 0) {
      setConfirming(0);
    }
  };

  const handleClick = () => {
    if (confirming) {
      resetConfirming();
      onClick();
    } else {
      setConfirming(delay);
      countdown.current = setInterval(() => setConfirming(x => x - 1), 1000);
    }
  };

  if (confirming === 0 && countdown.current) {
    resetConfirming();
  }

  let overrides = {};
  if (confirming) {
    overrides = {
      children: Translate.string('Click again to confirm ({delay})', {delay: confirming}),
      ...confirmOverrides,
    };
  }

  return (
    <Popup
      inverted
      position="left center"
      open={!!confirming && !!popupContent}
      trigger={<Button onClick={handleClick} {...rest} {...overrides} />}
    >
      {popupContent}
    </Popup>
  );
}

ConfirmButton.propTypes = {
  onClick: PropTypes.func.isRequired,
  delay: PropTypes.number,
  popupContent: PropTypes.node,
  confirmOverrides: PropTypes.object,
};

ConfirmButton.defaultProps = {
  delay: 5,
  popupContent: null,
  confirmOverrides: {color: 'orange'},
};
