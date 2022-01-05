// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Confirm} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

export default function RequestConfirm({
  requestFunc,
  confirmText,
  cancelText,
  onClose,
  ...confirmProps
}) {
  const [requestInProgress, setRequestInProgress] = useState(false);
  const confirmButton = (
    <Button disabled={requestInProgress} loading={requestInProgress}>
      {confirmText}
    </Button>
  );

  return (
    <Confirm
      {...confirmProps}
      onClose={onClose}
      onCancel={onClose}
      confirmButton={confirmButton}
      cancelButton={<Button disabled={requestInProgress}>{cancelText}</Button>}
      onConfirm={async () => {
        setRequestInProgress(true);
        const keepOpen = await requestFunc();
        setRequestInProgress(false);

        if (onClose && !keepOpen) {
          onClose();
        }
      }}
      closeIcon={!requestInProgress}
      closeOnDimmerClick={!requestInProgress}
      closeOnEscape={!requestInProgress}
    />
  );
}

RequestConfirm.propTypes = {
  requestFunc: PropTypes.func.isRequired,
  confirmText: PropTypes.string,
  cancelText: PropTypes.string,
  onClose: PropTypes.func,
  size: PropTypes.oneOf(['mini', 'tiny', 'small', 'large', 'fullscreen']),
};

RequestConfirm.defaultProps = {
  confirmText: Translate.string('Confirm'),
  cancelText: Translate.string('Cancel'),
  onClose: null,
  size: 'tiny',
};
