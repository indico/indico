// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {ReactElement} from 'react';

import {Icon, IconProps} from '../Icon';

import './Card.module.scss';

// HEADER COMPONENT
interface CardHeaderProps {
  children: React.ReactNode;
  styleName?: string;
}

export const CardHeader = ({children, styleName}: CardHeaderProps) => (
  <h6 styleName={`card-header ${styleName || ''}`}>{children}</h6>
);

type CardHeaderElement = ReactElement<CardHeaderProps, typeof CardHeader>;

// META DATA CATEGORY COMPONENT
interface CardMetaProps {
  children: React.ReactNode;
  styleName?: string;
}

export const CardMeta = ({children, styleName}: CardMetaProps) => (
  <p styleName={`card-meta ${styleName || ''}`}>{children}</p>
);

type CardMetaElement = ReactElement<CardMetaProps, typeof CardMeta>;

// DESCRIPTION COMPONENT
interface CardDescriptionProps {
  children: React.ReactNode;
  styleName?: string;
}

export const CardDescription = ({children, styleName}: CardDescriptionProps) => (
  <p styleName={`card-description ${styleName || ''}`}>{children}</p>
);

type CardDescriptionElement = ReactElement<CardDescriptionProps, typeof CardDescription>;

type CardIconElement = ReactElement<IconProps, typeof Icon>;

// CARD ROOT COMPONENT
type CardChild = CardIconElement | CardHeaderElement | CardMetaElement | CardDescriptionElement;

interface CardProps {
  children: CardChild | CardChild[];
  styleName?: string;
  href?: string;
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}

const CardRoot = ({children, href, onClick, styleName}: CardProps) => {
  if (href) {
    return (
      <a href={href} onClick={onClick} styleName={`card-root ${styleName || ''}`}>
        {children}
      </a>
    );
  }
  return <div styleName={`card-root ${styleName || ''}`}>{children}</div>;
};

type CardComponent = React.FunctionComponent<CardProps> & {
  Icon: typeof Icon;
  Header: typeof CardHeader;
  Meta: typeof CardMeta;
  Description: typeof CardDescription;
};

export const Card = Object.assign(CardRoot, {
  Icon,
  Header: CardHeader,
  Meta: CardMeta,
  Description: CardDescription,
}) as CardComponent;
