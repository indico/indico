// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {createContext, useContext, useState, ReactNode} from 'react';
import ReactDOM from 'react-dom';

import './Toast.module.scss';
import {Toast, ToastType} from './Toast';

export type ToastPosition = 'bottom-center' | 'top-center';

const TOAST_EXIT_DURATION = 200;
const DEFAULT_TOAST_DURATION = 3000;

export interface ToastOptions {
  type?: ToastType;
  message: ReactNode;
  duration?: number;
}
interface ToastItem extends ToastOptions {
  id: number;
  duration: number;
  type: ToastType;
  leaving?: boolean;
}

interface ToastContextValue {
  addToast: (options: ToastOptions) => void;
  removeToast: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

interface ToastProviderProps {
  children: ReactNode;
  position?: ToastPosition;
}

export function ToastProvider({children, position = 'top-center'}: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = (id: number) => {
    setToasts(current => current.map(t => (t.id === id ? {...t, leaving: true} : t)));
    window.setTimeout(
      () => setToasts(current => current.filter(t => t.id !== id)),
      TOAST_EXIT_DURATION
    );
  };

  const addToast = (options: ToastOptions) => {
    const id = Date.now() + Math.random();
    const toast: ToastItem = {
      id,
      type: options.type ?? 'info',
      message: options.message,
      duration: options.duration ?? DEFAULT_TOAST_DURATION,
    };
    setToasts(current => [...current, toast]);
    return id;
  };

  return (
    <ToastContext.Provider value={{addToast, removeToast}}>
      {children}
      {toasts.length > 0 &&
        ReactDOM.createPortal(
          <div styleName="toast-container" data-position={position}>
            {toasts.map(toast => (
              <Toast
                key={toast.id}
                id={toast.id}
                type={toast.type}
                message={toast.message}
                duration={toast.duration}
                leaving={toast.leaving}
                onClose={removeToast}
              />
            ))}
          </div>,
          document.body
        )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  return context;
}
