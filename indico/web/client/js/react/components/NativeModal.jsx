// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useRef} from 'react';
import ReactDOM from 'react-dom';
import {Button, Icon, Modal as SemanticModal} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {usePopupMountNode} from './PopupMountScope';

/** Modal dialog with native top-layer and focus behavior. */
export default function NativeModal({
  open,
  onClose,
  onMount,
  title,
  size,
  closeIcon,
  initialFocus,
  children,
  className,
  portal,
}) {
  const dialogRef = useRef(null);
  const parentMountNode = usePopupMountNode();
  const priorFocusRef = useRef(null);
  const onMountRef = useRef(onMount);
  onMountRef.current = onMount;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!open) {
      if (dialog.open) {
        dialog.close();
      }
      return undefined;
    }

    let frame;
    const show = () => {
      const parentDialog = portal
        ? parentMountNode?.closest('dialog')
        : dialog.parentElement.closest('dialog');
      if (parentDialog && !parentDialog.open) {
        frame = requestAnimationFrame(show);
        return;
      }
      if (!dialog.open) {
        priorFocusRef.current = document.activeElement;
        dialog.showModal();
        if (initialFocus === 'safe') {
          dialog.querySelector('.actions button')?.focus();
        } else if (initialFocus === 'close') {
          dialog.querySelector('.native-modal-close, .actions button')?.focus();
        } else {
          dialog.querySelector('.header h2, .header h3')?.focus();
          if (!dialog.contains(document.activeElement)) {
            dialog.focus();
          }
        }
        onMountRef.current?.();
      }
    };
    show();
    return () => {
      cancelAnimationFrame(frame);
      if (dialog.open) {
        dialog.close();
      }
      if (priorFocusRef.current?.isConnected) {
        priorFocusRef.current.focus();
      }
    };
  }, [open, initialFocus, portal, parentMountNode]);

  const handleCancel = event => {
    event.preventDefault();
    event.stopPropagation();
    onClose?.();
  };

  const handleKeyDown = event => {
    if (event.key === 'Escape') {
      event.stopPropagation();
      return;
    }
    if (event.key !== 'Tab' || event.target.closest('dialog') !== dialogRef.current) {
      return;
    }
    const focusable = [
      ...dialogRef.current.querySelectorAll(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ),
    ].filter(element => !element.disabled && element.getClientRects().length);
    if (!focusable.length) {
      event.preventDefault();
      dialogRef.current.focus();
      return;
    }
    if (
      event.shiftKey &&
      (document.activeElement === focusable[0] || document.activeElement.tabIndex < 0)
    ) {
      event.preventDefault();
      focusable[focusable.length - 1].focus();
    } else if (!event.shiftKey && document.activeElement === focusable[focusable.length - 1]) {
      event.preventDefault();
      focusable[0].focus();
    }
  };

  const content = (
    <dialog
      ref={dialogRef}
      className={`ui ${size} modal native-modal ${className}`}
      aria-label={title}
      onCancel={handleCancel}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      {closeIcon && (
        <button type="button" className="native-modal-close" onClick={onClose}>
          <Icon name="close" />
          <span className="native-modal-close-text">
            <Translate>Close</Translate>
          </span>
        </button>
      )}
      {children}
    </dialog>
  );
  return portal ? ReactDOM.createPortal(content, document.body) : content;
}

NativeModal.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  onMount: PropTypes.func,
  title: PropTypes.string.isRequired,
  size: PropTypes.string,
  closeIcon: PropTypes.bool,
  initialFocus: PropTypes.oneOf(['heading', 'safe', 'close']),
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  portal: PropTypes.bool,
};

NativeModal.defaultProps = {
  open: false,
  onClose: () => {},
  onMount: null,
  size: 'small',
  closeIcon: false,
  initialFocus: 'heading',
  className: '',
  portal: false,
};

NativeModal.Header = SemanticModal.Header;
NativeModal.Content = SemanticModal.Content;
NativeModal.Actions = SemanticModal.Actions;

/** Confirmation dialog with the safe action focused initially. */
export function NativeConfirm({
  header,
  content,
  confirmButton,
  cancelButton,
  open,
  onCancel,
  onConfirm,
}) {
  return (
    <NativeModal open={open} onClose={onCancel} title={header} size="small" initialFocus="safe">
      <NativeModal.Header>
        <h2>{header}</h2>
      </NativeModal.Header>
      <NativeModal.Content>{content}</NativeModal.Content>
      <NativeModal.Actions>
        <Button onClick={onCancel}>{cancelButton}</Button>
        {confirmButton && React.cloneElement(confirmButton, {onClick: onConfirm})}
      </NativeModal.Actions>
    </NativeModal>
  );
}

NativeConfirm.propTypes = {
  header: PropTypes.string.isRequired,
  content: PropTypes.node.isRequired,
  confirmButton: PropTypes.node,
  cancelButton: PropTypes.string.isRequired,
  open: PropTypes.bool,
  onCancel: PropTypes.func.isRequired,
  onConfirm: PropTypes.func,
};

NativeConfirm.defaultProps = {
  confirmButton: null,
  open: false,
  onConfirm: null,
};
