// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {ReactElement} from 'react';

import {Icon, IconProps} from '../../icon/Icon';
import Tag, {TagProps} from '../../tag/Tag';

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

type ListItemHeaderElement = ReactElement<ListItemHeaderProps, typeof ListItemHeader>;

type ListItemTagElement = ReactElement<TagProps, typeof Tag>;
type ListItemIconElement = ReactElement<IconProps, typeof Icon>;

type ListItemChild =
  | ListItemIconElement
  | ListItemHeaderElement
  | ListItemTagElement
  | React.ReactNode;

interface ListItemProps {
  children: ListItemChild | ListItemChild[];
  className?: string;
  href?: string;
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}

const ListItemRoot = ({children, href, onClick, className}: ListItemProps) => {
  if (href) {
    return (
      <a
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
    <div styleName="list-item-root" className={`indico-ui ${className ?? ''}`}>
      {children}
    </div>
  );
};

type ListItemComponent = React.FunctionComponent<ListItemProps> & {
  Icon: typeof Icon;
  Header: typeof ListItemHeader;
  Tag: typeof Tag;
};

export const ListItem = Object.assign(ListItemRoot, {
  Icon,
  Header: ListItemHeader,
  Tag,
}) as ListItemComponent;
