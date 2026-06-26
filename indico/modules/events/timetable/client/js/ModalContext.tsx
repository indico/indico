// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {createContext, useContext, useState} from 'react';

import {
  ContributionCreateForm,
  ContributionEditForm,
} from 'indico/modules/events/contributions/ContributionForm';

import TimetableManageModal from './TimetableManageModal';
import {TimetablePosterBlockModal} from './TimetablePosterBlockModal';
import {TimetableSessionCreateModal, TimetableSessionEditModal} from './TimetableSessionModal';
import {SessionBlockId} from './types';

export const DRAFT_ENTRY_MODAL = 'Create/Edit draft entry';
export const POSTER_BLOCK_CONTRIBUTIONS_MODAL = 'Show poster block contributions';
export const SESSION_CREATE_MODAL = 'Create session';
export const SESSION_EDIT_MODAL = 'Edit session';
export const UNSCHEDULED_CONTRIB_CREATE_MODAL = 'Create unscheduled contribution';
export const UNSCHEDULED_CONTRIB_EDIT_MODAL = 'Edit unscheduled contribution';

type ModalState =
  | {type: typeof DRAFT_ENTRY_MODAL; payload: {eventId: number; entry; onClose?}}
  | {type: typeof POSTER_BLOCK_CONTRIBUTIONS_MODAL; payload: {id: SessionBlockId}}
  | {type: typeof SESSION_CREATE_MODAL; payload: {onClose?: () => void}}
  | {type: typeof SESSION_EDIT_MODAL; payload: {sessionId: number; onClose?: () => void}}
  | {
      type: typeof UNSCHEDULED_CONTRIB_CREATE_MODAL;
      payload: {
        eventId: number;
        onCreate?: (contrib: any) => void;
        onClose?: () => void;
      };
    }
  | {
      type: typeof UNSCHEDULED_CONTRIB_EDIT_MODAL;
      payload: {
        eventId: number;
        contribId: number;
        onClose?: () => void;
      };
    };

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
            payload.onClose?.();
          }}
        />
      );
    case SESSION_CREATE_MODAL:
      return (
        <TimetableSessionCreateModal
          onClose={() => {
            closeModal();
            payload?.onClose?.();
          }}
        />
      );
    case SESSION_EDIT_MODAL:
      return (
        <TimetableSessionEditModal
          sessionId={payload.sessionId}
          onClose={() => {
            closeModal();
            payload?.onClose?.();
          }}
        />
      );
    case UNSCHEDULED_CONTRIB_CREATE_MODAL:
      return (
        <ContributionCreateForm
          eventId={payload.eventId}
          onClose={() => {
            closeModal();
            payload?.onClose?.();
          }}
          onCreate={payload?.onCreate}
          customFields={{}}
          customInitialValues={{}}
        />
      );
    case UNSCHEDULED_CONTRIB_EDIT_MODAL:
      return (
        <ContributionEditForm
          eventId={payload.eventId}
          contribId={payload.contribId}
          onClose={() => {
            closeModal();
            payload?.onClose?.();
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
