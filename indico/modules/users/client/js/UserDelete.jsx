// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import userDeleteURL from 'indico-url:users.user_delete';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Message, Modal, Icon, Input, Popup} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

const InfoState = 1;
const VerificationState = 2;

function UserDeleteDialogBody({
  dialogState: {currentState, gotToNextState},
  nameActions: {
    initialFirstName,
    initialLastName,
    firstName,
    lastName,
    onFirstNameChange,
    onLastNameChange,
  },
  disabled,
  inProgress,
  onDelete,
  onClose,
}) {
  return (
    <>
      <Modal.Header>
        <Translate>Delete user account</Translate>
      </Modal.Header>
      <Modal.Content>
        {currentState === InfoState && (
          <div>
            <Message negative>
              <Icon name="warning sign" />
              <Translate>Important notice</Translate>
            </Message>
            <p>
              <Translate>
                Are you sure you want to delete this user account? This is a destructive and
                permanent action. Once you delete this user, it cannot be recovered.
              </Translate>
            </p>
            <p>
              <Translate>To continue, click the button below.</Translate>
            </p>
          </div>
        )}

        {currentState === VerificationState && (
          <div>
            <p>
              <Translate>
                To confirm that you understand and accept the consequences of what you are about to
                do, type the first name "
                <Param name="fistName" wrapper={<strong />} value={initialFirstName} />" and the
                last name "<Param name="lastName" wrapper={<strong />} value={initialLastName} />"
                of the user below.
              </Translate>
            </p>
            <Translate as="label">First Name</Translate>
            <Input
              placeholder={Translate.string('First name')}
              value={firstName}
              onChange={onFirstNameChange}
              fluid
            />
            <br />
            <Translate as="label">Last Name</Translate>
            <Input
              placeholder={Translate.string('Last name')}
              value={lastName}
              onChange={onLastNameChange}
              fluid
            />
          </div>
        )}
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose} content={Translate.string('Cancel')} />
        {currentState === InfoState && (
          <Button color="red" onClick={gotToNextState}>
            <Translate>Yes, I want to delete this user</Translate>
          </Button>
        )}
        {currentState === VerificationState && (
          <Button color="red" onClick={onDelete} disabled={disabled} loading={inProgress}>
            <Translate>Delete user</Translate>
          </Button>
        )}
      </Modal.Actions>
    </>
  );
}

UserDeleteDialogBody.propTypes = {
  dialogState: PropTypes.object.isRequired,
  nameActions: PropTypes.object.isRequired,
  disabled: PropTypes.bool.isRequired,
  inProgress: PropTypes.bool.isRequired,
  onDelete: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

function UserDelete({userId, firstName: initialFirstName, lastName: initialLastName}) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [currentState, setCurrentState] = useState(InfoState);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const firstNameVerified = firstName === initialFirstName;
  const lastNameVerified = lastName === initialLastName;
  const isSameUser = userId === null;

  const gotToNextState = () => setCurrentState(VerificationState);

  const handleCloseDialog = () => {
    setCurrentState(InfoState);
    setFirstName('');
    setLastName('');
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

  const dialogState = {
    currentState,
    gotToNextState,
  };

  const nameActions = {
    initialFirstName,
    initialLastName,
    firstName,
    lastName,
    onFirstNameChange: (_, {value}) => setFirstName(value),
    onLastNameChange: (_, {value}) => setLastName(value),
  };

  return (
    <div>
      <p>
        <Translate>
          Once you delete this account, there is no going back. Please be certain. If you're not
          sure, consider using the "Block User" button above instead.
        </Translate>
      </p>
      <Popup
        position="top center"
        trigger={
          <span>
            <Button color="red" onClick={() => setIsDialogOpen(true)} disabled={isSameUser}>
              <Translate>Delete User</Translate>
            </Button>
          </span>
        }
        content={
          isSameUser
            ? Translate.string('You cannot delete your own account')
            : Translate.string('Delete user')
        }
      />
      {!isSameUser && (
        <Modal size="tiny" open={isDialogOpen} onClose={handleCloseDialog}>
          <UserDeleteDialogBody
            dialogState={dialogState}
            nameActions={nameActions}
            disabled={deleting || !firstNameVerified || !lastNameVerified}
            inProgress={deleting}
            onDelete={handleDelete}
            onClose={handleCloseDialog}
          />
        </Modal>
      )}
    </div>
  );
}

UserDelete.propTypes = {
  userId: PropTypes.number,
  firstName: PropTypes.string.isRequired,
  lastName: PropTypes.string.isRequired,
};

UserDelete.defaultProps = {
  userId: null,
};

window.setupUserDelete = function setupUserDelete(userId, firstName, lastName) {
  document.addEventListener('DOMContentLoaded', () => {
    ReactDOM.render(
      <UserDelete userId={userId} firstName={firstName} lastName={lastName} />,
      document.querySelector('#user-delete-container')
    );
  });
};
