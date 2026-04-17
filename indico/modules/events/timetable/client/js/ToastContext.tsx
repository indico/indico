// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {createContext, useContext, useState, ReactNode} from 'react';

import {Toast, ToastType} from './Toast';

export interface ToastOptions {
  type?: ToastType;
  message: ReactNode;
}

interface ToastContextValue {
  addToast: (options: ToastOptions) => void;
  removeToast: (id: number) => void;
}

interface ToastData extends ToastOptions {
  id: number;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({children}: {children: ReactNode}) {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const removeToast = (id: number) => {
    setToasts(currentToasts => currentToasts.filter(toast => toast.id !== id));
  };

  const addToast = (options: ToastOptions) => {
    const id = Date.now(); // Simple unique ID
    setToasts(currentToasts => [...currentToasts, {...options, id}]);

    // Auto-remove the toast after a few seconds
    // TODO: Customize the duration
    setTimeout(() => {
      removeToast(id);
    }, 3000);
  };

  return (
    <ToastContext.Provider value={{addToast, removeToast}}>
      {children}
      <>
        {toasts.map(toast => (
          <Toast key={toast.id} type={toast.type} message={toast.message} />
        ))}
      </>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  return context;
}
