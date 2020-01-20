// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Popup, Icon} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {useTimeout} from 'indico/react/hooks';

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
        <Icon
          style={copied ? {} : {cursor: 'pointer'}}
          disabled={copied}
          name="linkify"
          onClick={copied ? null : handleOpen}
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
