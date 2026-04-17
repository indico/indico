// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Icon} from 'semantic-ui-react';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

const ICONS: Record<ToastType, string> = {
  info: 'info',
  success: 'check',
  warning: 'warning',
  error: 'times',
};

interface ToastProps {
  type: ToastType;
  message: React.ReactNode;
}

export function Toast({type, message}: ToastProps) {
  return (
    <div data-type={type} role="status">
      <Icon name={ICONS[type]} styleName="toast-icon" />
      <div styleName="toast-message">{message}</div>
      <div styleName="toast-progress" />
    </div>
  );
}
