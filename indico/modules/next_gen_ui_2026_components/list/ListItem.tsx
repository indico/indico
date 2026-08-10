// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef, ReactElement} from 'react';

import {Icon, IconProps} from '../icon/Icon';
import {Tag, TagProps} from '../tag/Tag';
import './ListItem.module.scss';

interface ListItemHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const ListItemHeader = ({children, className}: ListItemHeaderProps) => (
  <h6 styleName="list-item-header" className={`indico-ui ${className || ''}`}>
    {children}
  </h6>
);

interface ListItemDetailsProps {
  children: React.ReactNode;
  className?: string;
}

export const ListItemDetails = ({children, className}: ListItemDetailsProps) => (
  <div styleName="list-item-details" className={`indico-ui ${className || ''}`}>
    {children}
  </div>
);

type ListItemHeaderElement = ReactElement<ListItemHeaderProps, typeof ListItemHeader>;
type ListItemDetailsElement = ReactElement<ListItemDetailsProps, typeof ListItemDetails>;
type ListItemTagElement = ReactElement<TagProps, typeof Tag>;
type ListItemIconElement = ReactElement<IconProps, typeof Icon>;

type ListItemChild =
  | ListItemIconElement
  | ListItemHeaderElement
  | ListItemDetailsElement
  | ListItemTagElement;

interface ListItemProps {
  children: ListItemChild | ListItemChild[];
  className?: string;
  href?: string;
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}

const ListItemRoot = forwardRef<HTMLAnchorElement | HTMLDivElement, ListItemProps>(
  ({children, href, onClick, className}, ref) => {
    if (href) {
      return (
        <a
          ref={ref as React.Ref<HTMLAnchorElement>}
          href={href}
          onClick={onClick}
          styleName="list-item-root"
          className={`indico-ui ${className ?? ''}`}
        >
          {children}
        </a>
      );
    }
    return (
      <div
        ref={ref as React.Ref<HTMLDivElement>}
        styleName="list-item-root"
        className={`indico-ui ${className ?? ''}`}
      >
        {children}
      </div>
    );
  }
);

ListItemRoot.displayName = 'ListItem';

type ListItemComponent = React.FunctionComponent<ListItemProps> & {
  Icon: typeof Icon;
  Header: typeof ListItemHeader;
  Details: typeof ListItemDetails;
  Tag: typeof Tag;
};

export const ListItem = Object.assign(ListItemRoot, {
  Icon,
  Header: ListItemHeader,
  Details: ListItemDetails,
  Tag,
}) as ListItemComponent;
