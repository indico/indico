// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Modal} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

export default function RequestConfirm({
  header,
  children,
  requestFunc,
  confirmText,
  cancelText,
  onClose,
  open,
  persistent,
  size,
  negative,
}) {
  const [requestInProgress, setRequestInProgress] = useState(false);
  const handleConfirmClick = async () => {
    setRequestInProgress(true);
    const keepOpen = await requestFunc();
    if (persistent && keepOpen) {
      // probably the request failed, so we clear the progress indicator
      setRequestInProgress(false);
    } else if (!persistent) {
      setRequestInProgress(false);

      if (onClose && !keepOpen) {
        onClose();
      }
    }
  };

  return (
    <Modal
      onClose={onClose}
      size={size}
      closeIcon={false}
      closeOnDimmerClick={!requestInProgress}
      closeOnEscape={!requestInProgress}
      open={open}
    >
      <Modal.Header>{header}</Modal.Header>
      <Modal.Content>{children}</Modal.Content>
      <Modal.Actions>
        <Button
          onClick={handleConfirmClick}
          disabled={requestInProgress}
          loading={requestInProgress}
          negative={negative}
          primary={!negative}
        >
          {confirmText}
        </Button>
        <Button onClick={onClose} disabled={requestInProgress}>
          {cancelText}
        </Button>
      </Modal.Actions>
    </Modal>
  );
}

RequestConfirm.propTypes = {
  header: PropTypes.node.isRequired,
  requestFunc: PropTypes.func.isRequired,
  children: PropTypes.node,
  open: PropTypes.bool.isRequired,
  confirmText: PropTypes.string,
  cancelText: PropTypes.string,
  onClose: PropTypes.func,
  size: PropTypes.oneOf(['mini', 'tiny', 'small', 'large', 'fullscreen']),
  /**
   * If the confirmation prompt is persistent, it will not close nor clear its "in progress"
   * state after
   */
  persistent: PropTypes.bool,
  /** Whether the confirmation is for a negative/dangerous action. */
  negative: PropTypes.bool,
};

RequestConfirm.defaultProps = {
  children: null,
  confirmText: Translate.string('Confirm'),
  cancelText: Translate.string('Cancel'),
  onClose: null,
  size: 'tiny',
  persistent: false,
  negative: false,
};

export function RequestConfirmDelete(props) {
  return (
    <RequestConfirm
      header={Translate.string('Confirm deletion')}
      confirmText={Translate.string('Delete')}
      negative
      {...props}
    />
  );
}

RequestConfirmDelete.propTypes = {
  ...RequestConfirm.propTypes,
  // eslint-disable-next-line react/require-default-props
  header: PropTypes.node,
};
