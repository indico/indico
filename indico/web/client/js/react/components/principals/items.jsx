// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon, List, Loader, Popup, Image, Label} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {PrincipalType} from './util';

import './items.module.scss';

export const PendingPrincipalListItem = ({type}) => (
  <PrincipalItem as={List.Item}>
    <div styleName="icon">
      <Icon name={PrincipalType.getIcon(type)} size="large" />
    </div>
    <PrincipalItem.Content name={PrincipalType.getPendingText(type)} />
    <div styleName="loader">
      <Loader active inline size="small" />
    </div>
  </PrincipalItem>
);

PendingPrincipalListItem.propTypes = {
  type: PrincipalType.propType,
};

PendingPrincipalListItem.defaultProps = {
  type: PrincipalType.user,
};

const PrincipalItemIcon = ({type, meta, invalid, avatarURL}) =>
  type === PrincipalType.eventRole || type === PrincipalType.categoryRole ? (
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
      ) : avatarURL ? (
        <Image src={avatarURL} size="mini" avatar />
      ) : (
        <Icon name={PrincipalType.getIcon(type)} size="large" />
      )}
    </div>
  );

PrincipalItemIcon.propTypes = {
  type: PropTypes.string,
  meta: PropTypes.object,
  invalid: PropTypes.bool,
  avatarURL: PropTypes.string,
};

PrincipalItemIcon.defaultProps = {
  type: PrincipalType.user,
  meta: {},
  invalid: false,
  avatarURL: null,
};

const PrincipalItemContent = ({name, detail, children}) => (
  <div styleName="content">
    <List.Content>{name}</List.Content>
    {detail && (
      <List.Description>
        <small>{detail}</small>
      </List.Description>
    )}
    {children}
  </div>
);

PrincipalItemContent.propTypes = {
  name: PropTypes.string.isRequired,
  detail: PropTypes.string,
  children: PropTypes.node,
};

PrincipalItemContent.defaultProps = {
  detail: null,
  children: null,
};

export const PrincipalItem = ({as, children, className, ...rest}) => {
  const Component = as || 'div';
  return (
    <Component styleName="item" className={className} {...rest}>
      {children}
    </Component>
  );
};

PrincipalItem.propTypes = {
  as: PropTypes.elementType,
  children: PropTypes.node,
  className: PropTypes.string,
};

PrincipalItem.defaultProps = {
  as: null,
  children: null,
  className: null,
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
  avatarURL,
}) => (
  <PrincipalItem as={List.Item}>
    <PrincipalItem.Icon type={type} meta={meta} invalid={invalid} avatarURL={avatarURL} />
    <PrincipalItem.Content name={name} detail={detail}>
      {actions && <div>{actions}</div>}
    </PrincipalItem.Content>
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
  </PrincipalItem>
);

PrincipalListItem.propTypes = {
  type: PrincipalType.propType,
  isPendingUser: PropTypes.bool,
  invalid: PropTypes.bool,
  name: PropTypes.string.isRequired,
  detail: PropTypes.string,
  meta: PropTypes.object,
  actions: PropTypes.node,
  onDelete: PropTypes.func,
  onAddFavorite: PropTypes.func,
  onDelFavorite: PropTypes.func,
  canDelete: PropTypes.bool,
  disabled: PropTypes.bool,
  readOnly: PropTypes.bool,
  favorite: PropTypes.bool,
  search: PropTypes.node,
  avatarURL: PropTypes.string,
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
  avatarURL: null,
  onDelete: null,
  onAddFavorite: null,
  onDelFavorite: null,
  favorite: false,
};

export const PersonListItem = ({
  type,
  meta,
  invalid,
  name,
  detail,
  avatarURL,
  children,
  canDelete,
  onDelete,
  onEdit,
  disabled,
  roles,
  onChangeRoles,
}) => (
  <PrincipalItem as={List.Item}>
    <PrincipalItem.Icon type={type} meta={meta} invalid={invalid} avatarURL={avatarURL} />
    <PrincipalItem.Content name={name} detail={detail}>
      {children}
    </PrincipalItem.Content>
    <div styleName="roles">
      {roles &&
        roles.map(({value, label, active}, idx) => (
          <Label
            as="a"
            size="small"
            key={value}
            color={active ? 'blue' : undefined}
            onClick={() =>
              onChangeRoles &&
              onChangeRoles(roles.map((r, i) => (i === idx ? {...r, active: !active} : r)))
            }
          >
            {label}
          </Label>
        ))}
    </div>
    <div styleName="actions">
      <Icon
        styleName="button edit"
        name="pencil alternate"
        size="large"
        onClick={onEdit}
        disabled={disabled}
      />
      {canDelete && (
        <Icon
          styleName="button delete"
          name="remove"
          size="large"
          onClick={onDelete}
          disabled={disabled}
        />
      )}
    </div>
  </PrincipalItem>
);

PersonListItem.propTypes = {
  type: PrincipalType.propType,
  invalid: PropTypes.bool,
  name: PropTypes.string.isRequired,
  detail: PropTypes.string,
  meta: PropTypes.object,
  onDelete: PropTypes.func,
  canDelete: PropTypes.bool,
  onEdit: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  avatarURL: PropTypes.string,
  children: PropTypes.node,
  roles: PropTypes.array,
  onChangeRoles: PropTypes.func,
};

PersonListItem.defaultProps = {
  type: PrincipalType.user,
  canDelete: true,
  disabled: false,
  invalid: false,
  detail: null,
  meta: {},
  avatarURL: null,
  onDelete: null,
  children: null,
  roles: null,
  onChangeRoles: null,
};

export const EmptyPrincipalListItem = ({search}) => (
  <PrincipalItem as={List.Item}>
    <div styleName="icon">
      <Icon name="user outline" size="large" />
    </div>
    <PrincipalItem.Content
      name={Translate.string('Nobody')}
      detail={Translate.string('Select a user')}
    />
    {search && <div styleName="actions">{search}</div>}
  </PrincipalItem>
);

EmptyPrincipalListItem.propTypes = {
  search: PropTypes.node,
};

EmptyPrincipalListItem.defaultProps = {
  search: null,
};

PrincipalItem.Icon = PrincipalItemIcon;
PrincipalItem.Content = PrincipalItemContent;
