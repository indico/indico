// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef, ReactElement} from 'react';

import {Button, ButtonProps} from 'indico/NGUI/button/Button';
import {Icon, IconProps} from 'indico/NGUI/icon/Icon';
import {Indicator, IndicatorProps} from 'indico/NGUI/indicator/Indicator';
import {Tag, TagProps} from 'indico/NGUI/tag/Tag';
import './ListItem.module.scss';
import {sharedClassName, NativeProps} from 'indico/NGUI/utils';

export type ListItemHeaderProps = NativeProps<'h6'>;

export const ListItemHeader = (props: ListItemHeaderProps) => {
  const {...nativeProps} = props;
  return (
    <p
      {...nativeProps}
      styleName="list-item-header"
      className={sharedClassName(nativeProps.className)}
    >
      {nativeProps.children}
    </p>
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

export const ListItemIndicator = (props: IndicatorProps) => {
  const {...nativeProps} = props;
  return (
    <Indicator
      {...nativeProps}
      className={sharedClassName(nativeProps.className)}
      position="top-right"
    />
  );
};

type ListItemHeaderElement = ReactElement<ListItemHeaderProps, typeof ListItemHeader>;
type ListItemDetailsElement = ReactElement<ListItemDetailsProps, typeof ListItemDetails>;
type ListItemTagElement = ReactElement<TagProps, typeof Tag>;
type ListItemIconElement = ReactElement<IconProps, typeof Icon>;
type ListItemButtonElement = ReactElement<ButtonProps, typeof Button>;
type ListItemIndicatorElement = ReactElement<IndicatorProps, typeof Indicator>;

type ListItemChild =
  | ListItemIconElement
  | ListItemHeaderElement
  | ListItemDetailsElement
  | ListItemTagElement
  | ListItemButtonElement
  | ListItemIndicatorElement;

type NativeLIElementProps = NativeProps<'li'>;
type NativeAnchorProps = NativeProps<'a'>;
type NativeDivProps = NativeProps<'div'>;

interface CustomListItemProps {
  children: ListItemChild | ListItemChild[];
  marker?: ReactElement;
  contentProps?: NativeDivProps | NativeAnchorProps;
}

export type ListItemProps = CustomListItemProps & NativeLIElementProps;

const ListItemRoot = forwardRef<HTMLLIElement, ListItemProps>((props, ref) => {
  const {children, marker, contentProps, ...nativeProps} = props;
  const rest = nativeProps as NativeLIElementProps;

  if (contentProps && 'href' in contentProps) {
    const anchorProps = contentProps as NativeAnchorProps;
    return (
      <li
        {...rest}
        styleName="list-item-wrapper"
        className={sharedClassName(rest.className)}
        ref={ref as React.Ref<HTMLLIElement>}
      >
        {marker}
        <a {...anchorProps} styleName="list-item-content" className={sharedClassName()}>
          {children}
        </a>
      </li>
    );
  }
  const divProps = contentProps as NativeDivProps;
  return (
    <li
      {...rest}
      ref={ref as React.Ref<HTMLLIElement>}
      styleName="list-item-wrapper"
      className={sharedClassName(rest.className)}
    >
      {marker}
      <div {...divProps} styleName="list-item-content" className={sharedClassName(rest.className)}>
        {children}
      </div>
    </li>
  );
});

ListItemRoot.displayName = 'ListItem';

type ListItemComponent = React.FunctionComponent<ListItemProps> & {
  Icon: typeof Icon;
  Header: typeof ListItemHeader;
  Details: typeof ListItemDetails;
  Tag: typeof Tag;
  Button: typeof Button;
  Indicator: typeof ListItemIndicator;
};

export const ListItem = Object.assign(ListItemRoot, {
  Icon,
  Header: ListItemHeader,
  Details: ListItemDetails,
  Tag,
  Button,
  Indicator: ListItemIndicator,
}) as ListItemComponent;

const ListComponent = forwardRef<HTMLUListElement, NativeProps<'ul'>>((props, ref) => {
  const {...nativeProps} = props;
  return (
    <ul
      {...nativeProps}
      ref={ref}
      styleName="list"
      className={sharedClassName(nativeProps.className)}
    >
      {nativeProps.children}
    </ul>
  );
});

ListComponent.displayName = 'List';

export const List = Object.assign(ListComponent, {
  Item: ListItem,
});
