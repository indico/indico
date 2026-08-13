// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef, ReactElement} from 'react';

import {Button, ButtonProps} from '../button/Button';
import {Icon, IconProps} from '../icon/Icon';
import {Tag, TagProps} from '../tag/Tag';
import './ListItem.module.scss';
import {sharedClassName, NativeProps} from '../utils';

export type ListItemHeaderProps = NativeProps<'h6'>;

export const ListItemHeader = (props: ListItemHeaderProps) => {
  const {...nativeProps} = props;
  return (
    <h6
      {...nativeProps}
      styleName="list-item-header"
      className={sharedClassName(nativeProps.className)}
    >
      {nativeProps.children}
    </h6>
  );
};

export type ListItemDetailsProps = NativeProps<'div'>;

export const ListItemDetails = (props: ListItemDetailsProps) => {
  const {...nativeProps} = props;
  return (
    <div
      {...nativeProps}
      styleName="list-item-details"
      className={sharedClassName(nativeProps.className)}
    >
      {nativeProps.children}
    </div>
  );
};

type ListItemHeaderElement = ReactElement<ListItemHeaderProps, typeof ListItemHeader>;
type ListItemDetailsElement = ReactElement<ListItemDetailsProps, typeof ListItemDetails>;
type ListItemTagElement = ReactElement<TagProps, typeof Tag>;
type ListItemIconElement = ReactElement<IconProps, typeof Icon>;
type ListItemButtonElement = ReactElement<ButtonProps, typeof Button>;

type ListItemChild =
  | ListItemIconElement
  | ListItemHeaderElement
  | ListItemDetailsElement
  | ListItemTagElement
  | ListItemButtonElement;

interface CustomListItemProps {
  children: ListItemChild | ListItemChild[];
}

export type ListItemProps = CustomListItemProps & NativeProps<'div'> & NativeProps<'a'>;

const ListItemRoot = forwardRef<HTMLAnchorElement | HTMLDivElement, ListItemProps>((props, ref) => {
  const {children, ...nativeProps} = props;
  if (nativeProps.href !== undefined) {
    return (
      <a
        {...nativeProps}
        ref={ref as React.Ref<HTMLAnchorElement>}
        href={nativeProps.href}
        styleName="list-item-root"
        className={sharedClassName(nativeProps.className)}
      >
        {children}
      </a>
    );
  }
  return (
    <div
      {...nativeProps}
      ref={ref as React.Ref<HTMLDivElement>}
      styleName="list-item-root"
      className={sharedClassName(nativeProps.className)}
    >
      {children}
    </div>
  );
});

ListItemRoot.displayName = 'ListItem';

type ListItemComponent = React.FunctionComponent<ListItemProps> & {
  Icon: typeof Icon;
  Header: typeof ListItemHeader;
  Details: typeof ListItemDetails;
  Tag: typeof Tag;
  Button: typeof Button;
};

export const ListItem = Object.assign(ListItemRoot, {
  Icon,
  Header: ListItemHeader,
  Details: ListItemDetails,
  Tag,
  Button,
}) as ListItemComponent;
