// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef, ReactElement} from 'react';

import {Icon, IconProps} from 'indico/NGUI/icon/Icon';
import './Card.module.scss';
import {NativeProps, sharedClassName} from 'indico/NGUI/utils';

export type CardHeaderProps = NativeProps<'h6'>;

export const CardHeader = ({...nativeProps}: CardHeaderProps) => (
  <h6 styleName="card-header" className={sharedClassName(nativeProps.className)}>
    {nativeProps.children}
  </h6>
);

export type CardMetaProps = NativeProps<'p'>;

export const CardMeta = ({...nativeProps}: CardMetaProps) => (
  <p styleName="card-meta" className={sharedClassName(nativeProps.className)}>
    {nativeProps.children}
  </p>
);

export type CardDescriptionProps = NativeProps<'p'>;

export const CardDescription = ({...nativeProps}: CardDescriptionProps) => (
  <p styleName="card-description" className={sharedClassName(nativeProps.className)}>
    {nativeProps.children}
  </p>
);

type CardMetaElement = ReactElement<CardMetaProps, typeof CardMeta>;
type CardHeaderElement = ReactElement<CardHeaderProps, typeof CardHeader>;
type CardDescriptionElement = ReactElement<CardDescriptionProps, typeof CardDescription>;
type CardIconElement = ReactElement<IconProps, typeof Icon>;

type CardChild = CardIconElement | CardHeaderElement | CardMetaElement | CardDescriptionElement;

interface CustomCardProps {
  children: CardChild | CardChild[];
}

type NativeAnchorProps = NativeProps<'a'>;
type NativeDivProps = NativeProps<'div'>;

type NativeUnion = ({href?: undefined} & NativeDivProps) | ({href: string} & NativeAnchorProps);
export type CardProps = CustomCardProps & NativeUnion;

const CardRoot = forwardRef<HTMLAnchorElement | HTMLDivElement, CardProps>(
  ({children, ...nativeProps}, ref) => {
    if (nativeProps.href !== undefined) {
      const rest = nativeProps as NativeAnchorProps;
      return (
        <a
          {...rest}
          ref={ref as React.Ref<HTMLAnchorElement>}
          styleName="card-root"
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
        styleName="card-root"
        className={sharedClassName(rest.className)}
      >
        {children}
      </div>
    );
  }
);

CardRoot.displayName = 'Card';

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
