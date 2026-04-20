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

export type ToastPosition = 'bottom-center';
const TOAST_POSITIONS: ToastPosition[] = ['bottom-center'];
const DEFAULT_TOAST_DURATION = 3000;

export interface ToastOptions {
  type?: ToastType;
  message: ReactNode;
  duration?: number;
  position?: ToastPosition;
}
interface ToastItem extends ToastOptions {
  id: number;
  duration: number;
  type: ToastType;
  position: ToastPosition;
}

interface ToastContextValue {
  addToast: (options: ToastOptions) => void;
  removeToast: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({children}: {children: ReactNode}) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = (id: number) => {
    setToasts(currentToasts => currentToasts.filter(toast => toast.id !== id));
  };

  const addToast = (options: ToastOptions) => {
    const id = Date.now() + Math.random();
    const toast: ToastItem = {
      id,
      type: options.type ?? 'info',
      message: options.message,
      duration: options.duration ?? DEFAULT_TOAST_DURATION,
      position: options.position ?? 'bottom-center',
    };
    setToasts(current => [...current, toast]);
    return id;
  };

  return (
    <ToastContext.Provider value={{addToast, removeToast}}>
      {children}
      {ReactDOM.createPortal(
        <>
          {TOAST_POSITIONS.map(position => {
            const positionToasts = toasts.filter(t => t.position === position);
            if (positionToasts.length === 0) {
              return null;
            }
            return (
              <div key={position} styleName="toast-container" data-position={position}>
                {positionToasts.map(toast => (
                  <Toast
                    key={toast.id}
                    id={toast.id}
                    type={toast.type}
                    message={toast.message}
                    duration={toast.duration}
                    onClose={removeToast}
                  />
                ))}
              </div>
            );
          })}
        </>,
        document.body
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  return context;
}
