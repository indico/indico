// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect} from 'react';
import {Icon, SemanticICONS} from 'semantic-ui-react';

import './Toast.module.scss';
import {Translate} from 'indico/react/i18n';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

const ICONS: Record<ToastType, SemanticICONS> = {
  info: 'info circle',
  success: 'check circle',
  warning: 'warning sign',
  error: 'times circle',
};

interface ToastProps {
  id: number;
  type: ToastType;
  message: React.ReactNode;
  duration: number;
  leaving?: boolean;
  onClose: (id: number) => void;
}

export function Toast({id, type, message, duration, leaving, onClose}: ToastProps) {
  useEffect(() => {
    if (leaving) {
      return undefined;
    }
    const timeoutId = window.setTimeout(() => onClose(id), duration);
    return () => window.clearTimeout(timeoutId);
  }, [id, duration, leaving, onClose]);

  return (
    <div
      styleName={leaving ? 'toast toast-leaving' : 'toast'}
      data-type={type}
      role="status"
      aria-live="polite"
    >
      <Icon name={ICONS[type]} styleName="toast-icon" />
      <div styleName="toast-message">{message}</div>
      <button
        type="button"
        styleName="toast-close"
        onClick={() => onClose(id)}
        aria-label={Translate.string('Close notification')}
      >
        <Icon name="close" />
      </button>
      <div styleName="toast-progress" style={{animationDuration: `${duration}ms`}} />
    </div>
  );
}
