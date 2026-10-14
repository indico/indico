// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Message, Modal, Icon, Popup} from 'semantic-ui-react';

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
  countdownSeconds,
}) => {
  const initialCountdown = Number.isFinite(Number(countdownSeconds)) ? Number(countdownSeconds) : 10;
  const [countdown, setCountdown] = useState(initialCountdown);
  const [isButtonDisabled, setButtonDisabled] = useState(true);

  useEffect(() => {
    if (open) {
      const start = Number.isFinite(Number(countdownSeconds)) ? Number(countdownSeconds) : 10;
      setCountdown(start);
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
  }, [open, countdownSeconds]);

  return (
    <Modal
      size="small"
      open={open}
      onClose={onClose}
      closeIcon={!isDeleting}
      closeOnEscape={!isDeleting}
      closeOnDimmerClick={!isDeleting}
    >
      <Modal.Header>{title}</Modal.Header>
      <Modal.Content>
        <Message negative icon>
          <Icon name="warning sign" />
          <Message.Content>
            <Message.Header>
              <Translate>This action is irreversible</Translate>
            </Message.Header>
            {message}
          </Message.Content>
        </Message>
        <div dangerouslySetInnerHTML={{__html: childrenHTML}} />
        <div>
          <Translate as="p">
            Are you sure you want to delete{' '}
            <Param name="recordName" wrapper={<strong />} value={recordName} />?
          </Translate>
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
            {confirmText || Translate.string('Delete')} (
            <Param name="countdown_seconds" value={countdown} />)
          </Button>
        ) : (
          <Button color="red" onClick={onDelete} disabled={isDeleting} loading={isDeleting}>
            {confirmText || Translate.string('Delete')}
          </Button>
        )}
      </Modal.Actions>
    </Modal>
  );
};

const GenericDeleteButton = ({
  title,
  buttonLabel,
  message,
  cancelText,
  confirmText,
  recordName,
  childrenHTML,
  deleteURL,
  redirectURL,
  isDisabled,
  disabledMessage,
  icon,
  iconColor,
  countdownSeconds,
  method,
  dataParams,
  buttonClass,
}) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const normalizedMethod = (method || 'DELETE').toUpperCase() === 'POST' ? 'POST' : 'DELETE';
  const normalizedDataParams = JSON.parse(dataParams) || {};

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      if (normalizedMethod === 'POST') {
        await indicoAxios.post(deleteURL, normalizedDataParams);
      } else {
        await indicoAxios.delete(deleteURL);
      }
    } catch (err) {
      setIsDeleting(false);
      setIsDialogOpen(false);
      handleAxiosError(err);
      return;
    }
    location.href = redirectURL || location.href;
  };
  if (isDisabled && disabledMessage) {
    return icon ? (
      <Popup
        trigger={
          <span>
            <Icon
              name={icon}
              color={iconColor || 'red'}
              style={{cursor: 'not-allowed', opacity: 0.5}}
            />
          </span>
        }
        size="small"
        wide
        content={disabledMessage}
        position="bottom center"
      />
    ) : (
      <Popup
        trigger={
          <span>
            <Button size="small" color="red" disabled>
              {buttonLabel}
            </Button>
          </span>
        }
        size="small"
        wide
        content={disabledMessage}
        position="bottom center"
      />
    );
  }

  const buttonProps = {};
  if (buttonClass === 'basic') {
    buttonProps.basic = true;
  }
  if (buttonClass === 'small') {
    buttonProps.size = 'small';
  }

  return (
    <>
      {icon ? (
        <Icon
          name={icon}
          color={iconColor || 'red'}
          style={{
            cursor: isDeleting || isDisabled ? 'not-allowed' : 'pointer',
            opacity: isDeleting || isDisabled ? 0.5 : 1,
          }}
          onClick={() => {
            if (!isDeleting && !isDisabled) {
              setIsDialogOpen(true);
            }
          }}
        />
      ) : (
        <Button
          {...buttonProps}
          color='red'
          onClick={() => setIsDialogOpen(true)}
          disabled={isDeleting || isDisabled}
        >
          {buttonLabel}
        </Button>
      )}
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
        countdownSeconds={countdownSeconds}
      />
    </>
  );
};

GenericDeleteButton.propTypes = {
  title: PropTypes.string.isRequired,
  buttonLabel: PropTypes.string,
  message: PropTypes.string.isRequired,
  confirmText: PropTypes.string.isRequired,
  deleteURL: PropTypes.string.isRequired,
  redirectURL: PropTypes.string,
  recordName: PropTypes.string.isRequired,
  childrenHTML: PropTypes.string,
  cancelText: PropTypes.string.isRequired,
  isDisabled: PropTypes.bool,
  disabledMessage: PropTypes.string,
  icon: PropTypes.string,
  iconColor: PropTypes.string,
  countdownSeconds: PropTypes.number,
  method: PropTypes.oneOf(['DELETE', 'POST']),
  dataParams: PropTypes.object,
  buttonClass: PropTypes.oneOf(['small', 'basic']),
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
  countdownSeconds: PropTypes.number,
};

DeleteDialog.defaultProps = {
  isDeleting: false,
  countdownSeconds: 10,
};

const tagName = 'ind-delete-button';

if (!customElements.get(tagName)) {
  customElements.define(
    tagName,
    class extends HTMLElement {
      connectedCallback() {
        requestAnimationFrame(() => {
          ReactDOM.render(
            <GenericDeleteButton
              title={this.getAttribute('dialog-title')}
              buttonLabel={this.getAttribute('button-label')}
              message={this.getAttribute('message')}
              cancelText={this.getAttribute('cancel-text')}
              confirmText={this.getAttribute('confirm-text')}
              recordName={this.getAttribute('record-name')}
              deleteURL={this.getAttribute('delete-url')}
              redirectURL={this.getAttribute('redirect-url')}
              isDisabled={JSON.parse(this.getAttribute('is-disabled') || 'false')}
              disabledMessage={this.getAttribute('disabled-message')}
              icon={this.getAttribute('icon')}
              iconColor={this.getAttribute('icon-color')}
              childrenHTML={this.innerHTML}
              countdownSeconds={this.getAttribute('countdown-seconds') || 10}
              method={this.getAttribute('method')}
              dataParams={this.getAttribute('data-params')}
              buttonClass={this.getAttribute('button-class') || undefined}
            />,
            this
          );
        });
      }
    }
  );
}

export {DeleteDialog, GenericDeleteButton};
export default GenericDeleteButton;
