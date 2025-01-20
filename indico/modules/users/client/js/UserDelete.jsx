// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import userDeleteURL from 'indico-url:users.user_delete';

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Message, Modal, Icon, List, Popup} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

function UserDeleteDialogBody({firstName, lastName, disabled, inProgress, onDelete, onClose}) {
  const [countdown, setCountdown] = useState(10);
  const [isButtonDisabled, setButtonDisabled] = useState(true);

  useEffect(() => {
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
  }, []);

  return (
    <>
      <Modal.Header>
        <Translate>
          Delete <Param name="first_name" value={firstName} />{' '}
          <Param name="last_name" value={lastName} />?
        </Translate>
      </Modal.Header>
      <Modal.Content>
        <Message negative icon>
          <Icon name="warning sign" />
          <Message.Content>
            <Message.Header>
              <Translate>This action is irreversible</Translate>
            </Message.Header>
            <Translate>Deleted user accounts cannot be restored.</Translate>
          </Message.Content>
        </Message>
        <Translate as="p">Once deleted, the following will happen:</Translate>
        <List style={{marginTop: 0}}>
          <List.Item>
            <List.Icon name="minus circle" />
            <List.Content>
              <Translate>
                <Param name="first_name" value={firstName} /> will no longer be able to access
                Indico.
              </Translate>
            </List.Content>
          </List.Item>
          <List.Item>
            <List.Icon name="times circle outline" />
            <List.Content>
              <Translate>
                <Param name="first_name" value={firstName} /> will be removed from all areas of
                Indico - this does not affect their presence in events as a speaker or other role;
                they will still be listed in such capacities where applicable.
              </Translate>
            </List.Content>
          </List.Item>
          <List.Item>
            <List.Icon name="trash alternate outline" />
            <List.Content>
              <Translate>
                Where it is not possible to delete <Param name="first_name" value={firstName} />,
                they will be anonymized and all personal data associated with the user will be
                removed from Indico.
              </Translate>
            </List.Content>
          </List.Item>
        </List>
        <Translate as="p">
          Are you sure you want to delete{' '}
          <Param wrapper={<strong />} name="first_name" value={firstName} />{' '}
          <Param wrapper={<strong />} name="last_name" value={lastName} />?
        </Translate>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose} content={Translate.string("No, I don't")} />
        {isButtonDisabled ? (
          <Button color="red" disabled>
            <Translate>
              Yes, I want to delete <Param name="first_name" value={firstName} /> (
              <Param name="countdown_seconds" value={countdown} />)
            </Translate>
          </Button>
        ) : (
          <Button color="red" onClick={onDelete} disabled={disabled} loading={inProgress}>
            <Translate>
              Yes, I want to delete <Param name="first_name" value={firstName} />
            </Translate>
          </Button>
        )}
      </Modal.Actions>
    </>
  );
}

UserDeleteDialogBody.propTypes = {
  firstName: PropTypes.string.isRequired,
  lastName: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
  inProgress: PropTypes.bool.isRequired,
  onDelete: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

function UserDelete({userId, firstName, lastName}) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const isSameUser = userId === null;

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
  };

  const handleDelete = async () => {
    setDeleting(true);
    let resp;
    try {
      resp = await indicoAxios.delete(userDeleteURL({user_id: userId}));
    } catch (err) {
      setDeleting(false);
      handleCloseDialog();
      handleAxiosError(err);
      return;
    }
    setDeleting(false);
    handleCloseDialog();
    location.href = resp.data.redirect;
  };

  return (
    <div>
      {isSameUser ? (
        <Popup
          trigger={
            <span>
              <Button size="small" color="red" disabled>
                <Translate>Delete User</Translate>
              </Button>
            </span>
          }
          size="small"
          wide
          content={Translate.string('You cannot delete your own account')}
          position="bottom center"
        />
      ) : (
        <>
          <Button size="small" color="red" onClick={() => setIsDialogOpen(true)}>
            <Translate>Delete User</Translate>
          </Button>
          <Modal size="small" open={isDialogOpen} onClose={handleCloseDialog} closeIcon>
            <UserDeleteDialogBody
              firstName={firstName}
              lastName={lastName}
              disabled={deleting}
              inProgress={deleting}
              onDelete={handleDelete}
              onClose={handleCloseDialog}
            />
          </Modal>
        </>
      )}
    </div>
  );
}

UserDelete.propTypes = {
  userId: PropTypes.oneOfType([PropTypes.number, PropTypes.oneOf([null])]),
  firstName: PropTypes.string.isRequired,
  lastName: PropTypes.string.isRequired,
};

customElements.define(
  'ind-user-delete-button',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <UserDelete
          userId={JSON.parse(this.getAttribute('user-id'))}
          firstName={this.getAttribute('user-first-name')}
          lastName={this.getAttribute('user-last-name')}
        />,
        this
      );
    }
  }
);
