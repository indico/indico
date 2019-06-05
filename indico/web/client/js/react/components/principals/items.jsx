// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Icon, List, Loader, Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

import './items.module.scss';

export const PendingPrincipalListItem = ({isGroup}) => (
  <List.Item>
    <div styleName="item">
      <div styleName="icon">
        <Icon name={isGroup ? 'users' : 'user'} size="large" />
      </div>
      <div styleName="content">
        <List.Content>
          {isGroup ? <Translate>Unknown group</Translate> : <Translate>Unknown user</Translate>}
        </List.Content>
      </div>
      <div styleName="loader">
        <Loader active inline size="small" />
      </div>
    </div>
  </List.Item>
);

PendingPrincipalListItem.propTypes = {
  isGroup: PropTypes.bool,
};

PendingPrincipalListItem.defaultProps = {
  isGroup: false,
};

export const PrincipalListItem = ({
  isPendingUser,
  isGroup,
  invalid,
  name,
  detail,
  canDelete,
  onDelete,
  onAddFavorite,
  onDelFavorite,
  disabled,
  readOnly,
  favorite,
  search,
  actions,
}) => (
  <List.Item>
    <div styleName="item">
      <div styleName="icon">
        {invalid ? (
          <Popup
            trigger={
              <Icon.Group size="large">
                <Icon name={isGroup ? 'users' : 'user'} />
                <Icon name="exclamation triangle" color="orange" corner />
              </Icon.Group>
            }
          >
            {isGroup ? (
              <Translate>
                This group does not exist anymore. Please choose a different one.
              </Translate>
            ) : (
              <Translate>This user does not exist anymore. Please choose someone else.</Translate>
            )}
          </Popup>
        ) : (
          <Icon name={isGroup ? 'users' : 'user'} size="large" />
        )}
      </div>
      <div styleName="content">
        <List.Content>{name}</List.Content>
        {detail && (
          <List.Description>
            <small>{detail}</small>
          </List.Description>
        )}
        {actions && <div>{actions}</div>}
      </div>
      {!readOnly && (
        <div styleName="actions">
          {!isGroup &&
            !isPendingUser &&
            (favorite ? (
              <Icon
                styleName="button favorite active"
                name="star"
                size="large"
                onClick={onDelFavorite}
                disabled={disabled}
              />
            ) : (
              <Icon
                styleName="button favorite"
                name="star outline"
                size="large"
                onClick={onAddFavorite}
                disabled={disabled}
              />
            ))}
          {canDelete && (
            <Icon
              styleName="button delete"
              name="remove"
              size="large"
              onClick={onDelete}
              disabled={disabled}
            />
          )}
          {search}
        </div>
      )}
    </div>
  </List.Item>
);

PrincipalListItem.propTypes = {
  isGroup: PropTypes.bool,
  isPendingUser: PropTypes.bool,
  invalid: PropTypes.bool,
  name: PropTypes.string.isRequired,
  detail: PropTypes.string,
  actions: PropTypes.node,
  onDelete: PropTypes.func.isRequired,
  onAddFavorite: PropTypes.func.isRequired,
  onDelFavorite: PropTypes.func.isRequired,
  canDelete: PropTypes.bool,
  disabled: PropTypes.bool,
  readOnly: PropTypes.bool,
  favorite: PropTypes.bool.isRequired,
  search: PropTypes.node,
};

PrincipalListItem.defaultProps = {
  canDelete: true,
  actions: null,
  disabled: false,
  readOnly: false,
  isGroup: false,
  isPendingUser: false,
  invalid: false,
  detail: null,
  search: null,
};

export const EmptyPrincipalListItem = ({search}) => (
  <List.Item>
    <div styleName="item">
      <div styleName="icon">
        <Icon name="user outline" size="large" />
      </div>
      <div styleName="content">
        <List.Content>
          <Translate>Nobody</Translate>
        </List.Content>
        <List.Description>
          <small>
            <Translate>Select a user</Translate>
          </small>
        </List.Description>
      </div>
      {search && <div styleName="actions">{search}</div>}
    </div>
  </List.Item>
);

EmptyPrincipalListItem.propTypes = {
  search: PropTypes.node,
};

EmptyPrincipalListItem.defaultProps = {
  search: null,
};
