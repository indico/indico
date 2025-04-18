// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Message, Modal, Icon} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

const DeleteDialog = ({
  open,
  title,
  message,
  childrenHTML,
  cancelText,
  confirmText,
  onDelete,
  onClose,
  isDeleting,
  recordName,
}) => {
  const [countdown, setCountdown] = useState(10);
  const [isButtonDisabled, setButtonDisabled] = useState(true);

  useEffect(() => {
    if (open) {
      setCountdown(10);
      setButtonDisabled(true);
      const timer = setInterval(() => {
        setCountdown(prevCountdown => {
          if (prevCountdown <= 1) {
            clearInterval(timer);
            setButtonDisabled(false);
            return 0;
          }
          return prevCountdown - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [open]);

  return (
    <Modal size="small" open={open} onClose={onClose} closeIcon={!isDeleting}>
      <Modal.Header>{title}</Modal.Header>
      <Modal.Content>
        <Message negative icon>
          <Icon name="warning sign" />
          <Message.Content>
            <Message.Header>
              <Translate>This action is irreversible</Translate>
            </Message.Header>
            <Translate>{message}</Translate>
          </Message.Content>
        </Message>
        <div dangerouslySetInnerHTML={{__html: childrenHTML}} />
        <div>
          <Translate as="p">Are you sure you want to delete {recordName}?</Translate>
        </div>
      </Modal.Content>
      <Modal.Actions>
        <Button
          onClick={onClose}
          disabled={isDeleting}
          content={cancelText || Translate.string('Cancel')}
        />
        {isButtonDisabled ? (
          <Button color="red" disabled>
            <Translate>
              {confirmText || Translate.string('Delete')} (
              <Param name="countdown_seconds" value={countdown} />)
            </Translate>
          </Button>
        ) : (
          <Button color="red" onClick={onDelete} disabled={isDeleting} loading={isDeleting}>
            <Translate>{confirmText || Translate.string('Delete')}</Translate>
          </Button>
        )}
      </Modal.Actions>
    </Modal>
  );
};

const GenericDeleteButton = ({
  title,
  buttonTitle,
  message,
  cancelText,
  confirmText,
  recordName,
  childrenHTML,
  deleteURL,
  redirectURL,
  isDisabled,
}) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await indicoAxios.delete(deleteURL);
    } catch (err) {
      setIsDeleting(false);
      setIsDialogOpen(false);
      handleAxiosError(err);
      return;
    }
    location.href = redirectURL || location.href;
  };

  return (
    <>
      <Button
        size="small"
        color="red"
        onClick={() => setIsDialogOpen(true)}
        disabled={isDeleting || isDisabled}
      >
        {buttonTitle}
      </Button>
      <DeleteDialog
        open={isDialogOpen}
        title={title}
        message={message}
        cancelText={cancelText}
        confirmText={confirmText}
        recordName={recordName}
        onDelete={handleDelete}
        onClose={() => setIsDialogOpen(false)}
        isDeleting={isDeleting}
        childrenHTML={childrenHTML}
      />
    </>
  );
};

GenericDeleteButton.propTypes = {
  title: PropTypes.string.isRequired,
  buttonTitle: PropTypes.string.isRequired,
  message: PropTypes.string.isRequired,
  confirmText: PropTypes.string.isRequired,
  deleteURL: PropTypes.string.isRequired,
  redirectURL: PropTypes.string,
  recordName: PropTypes.string.isRequired,
  childrenHTML: PropTypes.string,
  cancelText: PropTypes.string.isRequired,
  isDisabled: PropTypes.bool,
};

DeleteDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  message: PropTypes.string.isRequired,
  confirmText: PropTypes.string.isRequired,
  onDelete: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  isDeleting: PropTypes.bool,
  recordName: PropTypes.string.isRequired,
  childrenHTML: PropTypes.string,
  cancelText: PropTypes.string.isRequired,
};

DeleteDialog.defaultProps = {
  isDeleting: false,
};

customElements.define(
  'ind-delete-button',
  class extends HTMLElement {
    connectedCallback() {
      requestAnimationFrame(() => {
        ReactDOM.render(
          <GenericDeleteButton
            title={this.getAttribute('title')}
            buttonTitle={this.getAttribute('button-title')}
            message={this.getAttribute('message')}
            cancelText={this.getAttribute('cancel-text')}
            confirmText={this.getAttribute('confirm-text')}
            recordName={this.getAttribute('record-name')}
            deleteURL={this.getAttribute('delete-url')}
            redirectURL={this.getAttribute('redirect-url')}
            isDisabled={JSON.parse(this.getAttribute('is-disabled') || 'false')}
            childrenHTML={this.innerHTML}
          />,
          this
        );
      });
    }
  }
);

export default GenericDeleteButton;
