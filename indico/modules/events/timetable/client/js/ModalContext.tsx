// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {createContext, useContext, useState} from 'react';

import TimetableManageModal from './TimetableManageModal';
import {TimetablePosterBlockModal} from './TimetablePosterBlockModal';
import {SessionBlockId} from './types';

export const DRAFT_ENTRY_MODAL = 'Create/Edit draft entry';
export const POSTER_BLOCK_CONTRIBUTIONS_MODAL = 'Show poster block contributions';

type ModalState =
  | {type: typeof DRAFT_ENTRY_MODAL; payload: {eventId: number; entry; onClose?}}
  | {type: typeof POSTER_BLOCK_CONTRIBUTIONS_MODAL; payload: {id: SessionBlockId}};

type ModalType = ModalState['type'];

type ModalPayload<T extends ModalType> = Extract<ModalState, {type: T}>['payload'];

type ModalFunction = <T extends ModalType>(type: T, payload: ModalPayload<T>) => void;

interface ModalRootInterface {
  modal: ModalState | null;
  closeModal: () => void;
}

const ModalContext = createContext<ModalRootInterface & {openModal: ModalFunction}>(null);

function ModalRoot({modal, closeModal}: ModalRootInterface) {
  const {type, payload} = modal ?? {};
  switch (type) {
    case POSTER_BLOCK_CONTRIBUTIONS_MODAL:
      return <TimetablePosterBlockModal id={payload.id} onClose={closeModal} />;
    case DRAFT_ENTRY_MODAL:
      return (
        <TimetableManageModal
          eventId={payload.eventId}
          entry={payload.entry}
          onClose={() => {
            closeModal();

            if (payload.onClose) {
              payload?.onClose();
            }
          }}
        />
      );
    default:
      return null;
  }
}

/**
 * ModalProvider centralizes modal management for the application.
 *
 * Instead of rendering and controlling individual modals in every component,
 * this provider allows you to open and close modals from anywhere using the context.
 */
export function ModalProvider({children}: {children: React.ReactNode}) {
  const [modal, setModal] = useState<ModalState | null>(null);

  const openModal: ModalFunction = (type, payload) => setModal({type, payload} as ModalState);
  const closeModal = () => setModal(null);

  return (
    <ModalContext.Provider value={{modal, openModal, closeModal}}>
      {children}
      <ModalRoot modal={modal} closeModal={closeModal} />
    </ModalContext.Provider>
  );
}

export function useModal() {
  return useContext(ModalContext);
}
