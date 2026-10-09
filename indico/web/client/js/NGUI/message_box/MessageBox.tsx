// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {Icon, IconColor} from 'indico/NGUI/icon/Icon';
import {MessageBoxType} from 'indico/NGUI/tokens';
import {NativeProps, sharedClassName} from 'indico/NGUI/utils';

import './MessageBox.module.scss';

// TODO: Reconsider neccessity of fixedWidth prop

interface CustomMessageBoxProps {
  type: MessageBoxType;
  message?: string;
  icon?: boolean;
  largeIcon?: boolean;
  fixedWidth?: boolean;
  noBorder?: boolean;
  customIcon?: string;
}

export type MessageBoxProps = NativeProps<'div'> & CustomMessageBoxProps;

export default function MessageBox({
  type,
  message,
  icon = true,
  largeIcon = false,
  fixedWidth = false,
  noBorder = false,
  customIcon,
  ...nativeProps
}: MessageBoxProps) {
  const iconMapping: Record<MessageBoxType, string> = {
    info: 'circle-info',
    warning: 'triangle-exclamation',
    error: 'circle-xmark',
    highlight: 'lightbulb',
    danger: 'circle-exclamation',
    success: 'circle-check',
  };

  const colorMapping: Record<MessageBoxType, IconColor> = {
    info: 'gray',
    warning: 'warning',
    error: 'error',
    highlight: 'primary',
    danger: 'error',
    success: 'success',
  };

  return (
    <div
      className={sharedClassName(
        fixedWidth ? `${nativeProps.className} fixed-width` : nativeProps.className
      )}
      styleName="message-box"
      data-type={type}
      data-no-border={noBorder}
      {...nativeProps}
    >
      {icon && (
        <Icon
          icon={customIcon || `fas:${iconMapping[type]}`}
          compact
          size={largeIcon ? 'xxxxl' : 'xl'}
          color={colorMapping[type]}
          styleName="message-box-icon"
        />
      )}
      {(message || nativeProps.children) && (
        <div styleName="message-box-content">
          {message} {nativeProps.children}
        </div>
      )}
    </div>
  );
}
