// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Popup, Button} from 'semantic-ui-react';

import {useTimeout} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

export default function ClipboardButton({text, successText}) {
  const [copied, setCopied] = useState(false);
  useTimeout(() => setCopied(false), copied ? 2000 : null);

  const handleOpen = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
  };

  const handleClose = () => {
    setCopied(false);
  };

  return (
    <Popup
      on="click"
      position="bottom center"
      trigger={
        <Button
          basic
          type="button"
          icon="linkify"
          onClick={handleOpen}
          style={copied ? {} : {cursor: 'pointer'}}
          disabled={copied}
          circular
        />
      }
      open={copied}
      onClose={handleClose}
      content={successText || Translate.string('Text copied')}
    />
  );
}

ClipboardButton.propTypes = {
  text: PropTypes.string.isRequired,
  successText: PropTypes.string,
};

ClipboardButton.defaultProps = {
  successText: null,
};
