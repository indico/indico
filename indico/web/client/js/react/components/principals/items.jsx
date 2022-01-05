// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon, List, Loader, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {PrincipalType} from './util';

import './items.module.scss';

export const PendingPrincipalListItem = ({type}) => (
  <List.Item>
    <div styleName="item">
      <div styleName="icon">
        <Icon name={PrincipalType.getIcon(type)} size="large" />
      </div>
      <div styleName="content">
        <List.Content>{PrincipalType.getPendingText(type)}</List.Content>
      </div>
      <div styleName="loader">
        <Loader active inline size="small" />
      </div>
    </div>
  </List.Item>
);

PendingPrincipalListItem.propTypes = {
  type: PrincipalType.propType,
};

PendingPrincipalListItem.defaultProps = {
  type: PrincipalType.user,
};

export const PrincipalListItem = ({
  isPendingUser,
  type,
  invalid,
  name,
  detail,
  meta,
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
      {type === PrincipalType.eventRole || type === PrincipalType.categoryRole ? (
        <div styleName="event-role">
          <span style={meta.style}>{meta.code}</span>
        </div>
      ) : (
        <div styleName="icon">
          {invalid ? (
            <Popup
              trigger={
                <Icon.Group size="large">
                  <Icon name={PrincipalType.getIcon(type)} />
                  <Icon name="exclamation triangle" color="orange" corner />
                </Icon.Group>
              }
            >
              {PrincipalType.getDeletedText(type)}
            </Popup>
          ) : (
            <Icon name={PrincipalType.getIcon(type)} size="large" />
          )}
        </div>
      )}
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
          {type === PrincipalType.user &&
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
  type: PrincipalType.propType,
  isPendingUser: PropTypes.bool,
  invalid: PropTypes.bool,
  name: PropTypes.string.isRequired,
  detail: PropTypes.string,
  meta: PropTypes.object,
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
  type: PrincipalType.user,
  canDelete: true,
  actions: null,
  disabled: false,
  readOnly: false,
  isPendingUser: false,
  invalid: false,
  detail: null,
  meta: {},
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
