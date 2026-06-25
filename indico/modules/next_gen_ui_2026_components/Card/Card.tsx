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
  className?: string;
}

export const CardHeader = ({children, className}: CardHeaderProps) => (
  <h6 styleName="card-header" className={`indico-ui ${className || ''}`}>
    {children}
  </h6>
);

type CardHeaderElement = ReactElement<CardHeaderProps, typeof CardHeader>;

// META DATA CATEGORY COMPONENT
interface CardMetaProps {
  children: React.ReactNode;
  className?: string;
}

export const CardMeta = ({children, className}: CardMetaProps) => (
  <p styleName='card-meta' className={`indico-ui ${className || ''}`}>
    {children}
  </p>
);

type CardMetaElement = ReactElement<CardMetaProps, typeof CardMeta>;

// DESCRIPTION COMPONENT
interface CardDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const CardDescription = ({children, className}: CardDescriptionProps) => (
  <p styleName='card-description' className={`indico-ui ${className || ''}`}>
    {children}
  </p>
);

type CardDescriptionElement = ReactElement<CardDescriptionProps, typeof CardDescription>;

type CardIconElement = ReactElement<IconProps, typeof Icon>;

// CARD ROOT COMPONENT
type CardChild = CardIconElement | CardHeaderElement | CardMetaElement | CardDescriptionElement;

interface CardProps {
  children: CardChild | CardChild[];
  className?: string;
  href?: string;
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
  ariaLabel?: string;
}

const CardRoot = ({children, href, onClick, className, ariaLabel}: CardProps) => {
  if (href) {
    return (
      <a
        href={href}
        onClick={onClick}
        styleName="card-root"
        className={`indico-ui ${className ?? ''}`}
        aria-label={ariaLabel}
      >
        {children}
      </a>
    );
  }
  return (
    <div styleName="card-root" className={`indico-ui ${className ?? ''}`} aria-label={ariaLabel}>
      {children}
    </div>
  );
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
