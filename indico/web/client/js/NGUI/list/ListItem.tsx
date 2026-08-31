// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef, ReactElement} from 'react';

import {Button, ButtonProps} from 'indico/NGUI/button/Button';
import {Icon, IconProps} from 'indico/NGUI/icon/Icon';
import {Tag, TagProps} from 'indico/NGUI/tag/Tag';
import './ListItem.module.scss';
import {sharedClassName, NativeProps} from 'indico/NGUI/utils';

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

type NativeDivProps = NativeProps<'div'>;
type NativeAnchorProps = NativeProps<'a'>;
type NativeUnion = ({href?: undefined} & NativeDivProps) | ({href: string} & NativeAnchorProps);
export type ListItemProps = CustomListItemProps & NativeUnion;

const ListItemRoot = forwardRef<HTMLAnchorElement | HTMLDivElement, ListItemProps>((props, ref) => {
  const {children, ...nativeProps} = props;
  if (nativeProps.href !== undefined) {
    const rest = nativeProps as NativeAnchorProps;
    return (
      <a
        {...rest}
        ref={ref as React.Ref<HTMLAnchorElement>}
        styleName="list-item-root"
        className={sharedClassName(rest.className)}
      >
        {children}
      </a>
    );
  }
  const rest = nativeProps as NativeDivProps;
  return (
    <div
      {...rest}
      ref={ref as React.Ref<HTMLDivElement>}
      styleName="list-item-root"
      className={sharedClassName(rest.className)}
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
