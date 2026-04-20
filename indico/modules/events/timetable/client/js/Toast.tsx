// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Icon} from 'semantic-ui-react';

import './Toast.module.scss';
import {Translate} from 'indico/react/i18n';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

const ICONS: Record<ToastType, string> = {
  info: 'info',
  success: 'check',
  warning: 'warning',
  error: 'times',
};

interface ToastProps {
  id: number;
  type: ToastType;
  message: React.ReactNode;
  duration: number;
  onClose: (id: number) => void;
}

export function Toast({id, type, message, duration, onClose}: ToastProps) {
  // useEffect(() => {
  //   const timeoutId = window.setTimeout(() => onClose(id), duration);
  //   return () => window.clearTimeout(timeoutId);
  // }, [id, duration, onClose]);

  return (
    <div styleName="toast" data-type={type} role="status" aria-live="polite">
      <Icon name={ICONS[type]} styleName="toast-icon" />
      <div styleName="toast-message">{message}</div>
      <button
        type="button"
        onClick={() => onClose(id)}
        aria-label={Translate.string('Close notification')}
      >
        <Icon name="close" />
      </button>
      <div styleName="toast-progress" style={{animationDuration: `${duration}ms`}} />
    </div>
  );
}
