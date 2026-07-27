// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {ReactElement} from 'react';

import {Dot} from '../dot/Dot';
import {Icon, IconProps} from '../icon/Icon';
import Tag, {TagProps} from '../tag/Tag';
import './ListItem.module.scss';
import {LegacyColor} from '../tokens';

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

interface LabelIndicatorProps {
  color: LegacyColor;
  label: string;
  className?: string;
}

export function LabelIndicator({color, label, className}: LabelIndicatorProps) {
  return (
    <div styleName="label-indicator" className={`indico-ui ${className || ''}`}>
      <Dot styleName="dot" color={color} size="xxs" />
      <p styleName="label-indicator-text">{label}</p>
    </div>
  );
}

type ListItemHeaderElement = ReactElement<ListItemHeaderProps, typeof ListItemHeader>;
type ListItemDetailsElement = ReactElement<ListItemDetailsProps, typeof ListItemDetails>;
type ListItemTagElement = ReactElement<TagProps, typeof Tag>;
type ListItemIconElement = ReactElement<IconProps, typeof Icon>;
type ListItemLabelIndicatorElement = ReactElement<LabelIndicatorProps, typeof LabelIndicator>;

type ListItemChild =
  | ListItemIconElement
  | ListItemHeaderElement
  | ListItemDetailsElement
  | ListItemTagElement
  | ListItemLabelIndicatorElement
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
  Details: typeof ListItemDetails;
  Tag: typeof Tag;
  LabelIndicator: typeof LabelIndicator;
};

export const ListItem = Object.assign(ListItemRoot, {
  Icon,
  Header: ListItemHeader,
  Details: ListItemDetails,
  Tag,
  LabelIndicator,
}) as ListItemComponent;
