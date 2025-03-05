// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import userBlockURL from 'indico-url:users.user_block';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Modal, Icon, Popup, Header} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

function UserBlockModalBody({firstName, lastName, isUserBlocked, inProgress, onBlock, onClose}) {
  return (
    <>
      <Modal.Header>
        {isUserBlocked ? (
          <Translate>
            Unblock <Param name="first_name" value={firstName} />{' '}
            <Param name="last_name" value={lastName} />?
          </Translate>
        ) : (
          <Translate>
            Block <Param name="first_name" value={firstName} />{' '}
            <Param name="last_name" value={lastName} />?
          </Translate>
        )}
      </Modal.Header>
      <Modal.Content>
        <Header as="h3" icon textAlign="center" style={{marginBottom: 0}}>
          {isUserBlocked ? (
            <>
              <Icon name="unlock alternate" />
              <Translate>
                Are you sure you want to unblock <Param name="first_name" value={firstName} />?
              </Translate>
            </>
          ) : (
            <>
              <Icon name="hand paper outline" />
              <Translate>
                Are you sure you want to block <Param name="first_name" value={firstName} />?
              </Translate>
            </>
          )}

          <Header.Subheader style={{marginTop: '0.5em', color: 'unset'}}>
            {isUserBlocked ? (
              <Translate>
                <Param name="first_name" wrapper={<strong />} value={firstName} />{' '}
                <Param name="last_name" wrapper={<strong />} value={lastName} /> will regain access
                to Indico.
              </Translate>
            ) : (
              <Translate>
                <Param name="first_name" wrapper={<strong />} value={firstName} />{' '}
                <Param name="last_name" wrapper={<strong />} value={lastName} /> will no longer be
                able to access Indico.
              </Translate>
            )}
          </Header.Subheader>
        </Header>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose} disabled={inProgress}>
          <Translate>Cancel</Translate>
        </Button>
        <Button
          negative={!isUserBlocked}
          primary={isUserBlocked}
          onClick={onBlock}
          disabled={inProgress}
          loading={inProgress}
        >
          {isUserBlocked ? (
            <Translate>
              Unblock <Param name="first_name" value={firstName} />
            </Translate>
          ) : (
            <Translate>
              Block <Param name="first_name" value={firstName} />
            </Translate>
          )}
        </Button>
      </Modal.Actions>
    </>
  );
}

UserBlockModalBody.propTypes = {
  firstName: PropTypes.string.isRequired,
  lastName: PropTypes.string.isRequired,
  isUserBlocked: PropTypes.bool.isRequired,
  inProgress: PropTypes.bool.isRequired,
  onBlock: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

function UserBlock({userId, isUserBlocked, firstName, lastName}) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [inProgress, setInProgress] = useState(false);
  const isSameUser = userId === Indico.User.id;

  const blockUser = async () => {
    setInProgress(true);
    try {
      await indicoAxios({
        url: userBlockURL({user_id: userId}),
        method: isUserBlocked ? 'DELETE' : 'PUT',
      });
      location.reload();
    } catch (error) {
      handleAxiosError(error);
      setInProgress(false);
    }
  };

  return (
    <div>
      {isSameUser ? (
        <Popup
          trigger={
            <span>
              <Button size="small" color="orange" disabled>
                <Translate>Block User</Translate>
              </Button>
            </span>
          }
          size="small"
          wide
          content={Translate.string('You cannot block yourself')}
          position="bottom center"
        />
      ) : (
        <>
          <Button
            size="small"
            color={isUserBlocked ? null : 'orange'}
            onClick={() => setIsDialogOpen(true)}
          >
            {isUserBlocked ? Translate.string('Unblock User') : Translate.string('Block User')}
          </Button>
          <Modal size="tiny" open={isDialogOpen} onClose={() => setIsDialogOpen(false)} closeIcon>
            <UserBlockModalBody
              firstName={firstName}
              lastName={lastName}
              isUserBlocked={isUserBlocked}
              inProgress={inProgress}
              onBlock={blockUser}
              onClose={() => setIsDialogOpen(false)}
            />
          </Modal>
        </>
      )}
    </div>
  );
}

UserBlock.propTypes = {
  userId: PropTypes.number.isRequired,
  isUserBlocked: PropTypes.bool.isRequired,
  firstName: PropTypes.string.isRequired,
  lastName: PropTypes.string.isRequired,
};

customElements.define(
  'ind-user-block-button',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <UserBlock
          userId={JSON.parse(this.getAttribute('user-id'))}
          isUserBlocked={JSON.parse(this.getAttribute('user-is-blocked'))}
          firstName={this.getAttribute('user-first-name')}
          lastName={this.getAttribute('user-last-name')}
        />,
        this
      );
    }
  }
);
